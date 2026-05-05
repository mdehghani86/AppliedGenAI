"""
Smoke-test a notebook end-to-end-ish:
  - Read code cells in order.
  - Skip cells that are pure Colab UX (file uploads, drive mount, interactive
    secrets prompts that don't fall back) or that re-install packages.
  - Strip IPython magic (%, !).
  - Execute under a single namespace with a per-cell timeout.
  - Stop and report at the first error.

Designed for diagnostic value, not 100% fidelity to a real Colab run.
"""
from __future__ import annotations

import io
import json
import os
import re
import signal
import sys
import threading
import traceback
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

# Force UTF-8 console output on Windows so emoji-laden tracebacks print cleanly.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKIP_PATTERNS = [
    # Cell-level skips (only when the cell is essentially just one of these).
    r"files\.upload\(",         # interactive Colab UI
    r"drive\.mount\(",          # Colab drive mount
    r"/content/drive/",         # any reference to a Colab-mounted drive path
    r"-----",                   # student fill-in-the-blank exercises (by design invalid)
]

# Per-line strips (lines matching these are dropped, but the cell is kept).
LINE_DROP_PATTERNS = [
    r"^\s*!",                   # any shell magic (!pip, !wget, !curl, ...)
    r"^\s*%",                   # cell/line magic
    r"^\s*from\s+google\.colab", # Colab-only import (we provide a stub)
    r"^\s*import\s+google\.colab",
    r".*get_ipython\(\)",
]


# Injected at the start of each notebook's namespace so that any cell which
# does `userdata.get("OPENAI_API_KEY")` (after we've dropped the colab import)
# still resolves to the real env var. We also stub `input` so labs that have a
# top-level interactive `input()` call don't block the harness — and labs with
# `input()` inside a function definition still load cleanly.
_USERDATA_STUB = """
import builtins as _builtins
import os as _os
class _UserDataStub:
    def get(self, name):
        return _os.environ.get(name)
userdata = _UserDataStub()

_real_input = _builtins.input
def _stub_input(prompt=""):
    raise RuntimeError("smoke-test: top-level input() is not supported")
_builtins.input = _stub_input
input = _stub_input
"""

CELL_TIMEOUT = 25  # seconds


def cell_should_skip(src: str) -> bool:
    return any(re.search(p, src, re.MULTILINE) for p in SKIP_PATTERNS)


def strip_magic(src: str) -> str:
    """Replace lines matching LINE_DROP_PATTERNS with `pass` (preserving the
    original indent), so a dropped line that was the sole body of an `if`/`try`
    block doesn't leave an empty block behind. Also follows backslash line
    continuations so a `!pip install -U \\` followed by indented package names
    is dropped entirely (otherwise the orphan continuation lines become a
    syntax error)."""
    drops = [re.compile(p) for p in LINE_DROP_PATTERNS]
    lines = src.splitlines(True)
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if any(d.match(line) for d in drops):
            indent = line[: len(line) - len(line.lstrip())]
            out.append(f"{indent}pass\n")
            # Skip backslash-continuation lines that follow.
            while line.rstrip("\n").endswith("\\") and i + 1 < len(lines):
                i += 1
                line = lines[i]
            i += 1
            continue
        out.append(line)
        i += 1
    return "".join(out)


class TimeoutError_(Exception): ...


def _run_with_timeout(code: str, ns: dict, timeout: int) -> tuple[bool, str]:
    """Run `code` in namespace `ns` under `timeout` seconds. Returns (ok, msg)."""
    err = {}

    def target():
        try:
            exec(compile(code, "<cell>", "exec"), ns)
        except BaseException:
            err["tb"] = traceback.format_exc(limit=4)

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return False, f"TIMEOUT after {timeout}s"
    if "tb" in err:
        return False, err["tb"]
    return True, ""


# Ensure the repo root (cwd) is on sys.path so `from utils import ...` works.
if "" not in sys.path and "." not in sys.path:
    sys.path.insert(0, "")


def run_notebook(path: Path, max_cells: int | None = None) -> dict:
    nb = json.loads(path.read_text(encoding="utf-8"))
    ns: dict = {"__name__": "__main__"}
    # Pre-populate the namespace with a userdata stub.
    exec(_USERDATA_STUB, ns)
    summary = {"path": path.name, "cells_run": 0, "cells_skipped": 0,
               "first_error_cell": None, "first_error": None, "stopped_after": None}
    code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
    if max_cells:
        code_cells = code_cells[:max_cells]

    for idx, cell in enumerate(code_cells):
        src = "".join(cell["source"])
        if not src.strip():
            continue
        if cell_should_skip(src):
            summary["cells_skipped"] += 1
            continue
        clean = strip_magic(src)
        if not clean.strip():
            summary["cells_skipped"] += 1
            continue

        # Suppress prints to keep output tight.
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            ok, msg = _run_with_timeout(clean, ns, CELL_TIMEOUT)
        summary["cells_run"] += 1
        if os.environ.get("SMOKE_DEBUG"):
            sys.stderr.write(f"   cell#{idx}/{len(code_cells)} run, ok={ok}, ns_keys={len(ns)}, src_len={len(clean)}\n")
        if not ok:
            # Trim noise from tracebacks.
            short = msg.strip().splitlines()
            short_msg = "\n".join(short[-3:]) if short else msg
            summary["first_error_cell"] = idx
            summary["first_error"] = short_msg
            summary["stopped_after"] = summary["cells_run"]
            return summary
    return summary


if __name__ == "__main__":
    args = sys.argv[1:]
    max_cells = None
    if args and args[0].startswith("--max="):
        max_cells = int(args[0].split("=", 1)[1])
        args = args[1:]
    targets = args or sorted(str(p) for p in Path(".").glob("*.ipynb"))
    for t in targets:
        s = run_notebook(Path(t), max_cells=max_cells)
        if s["first_error"]:
            print(f"FAIL  {s['path']:55} cells {s['stopped_after']}/{s['cells_run']+s['cells_skipped']}  -> {s['first_error'].splitlines()[-1][:140]}")
        else:
            print(f"PASS  {s['path']:55} {s['cells_run']} ran, {s['cells_skipped']} skipped")
