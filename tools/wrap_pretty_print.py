"""
Pass 2 of the 2026-05 refresh: across all notebooks,

  (a) finish the v0 → v1 OpenAI SDK migration anywhere it was missed
      (currently only Prompting_with_API still had legacy calls), and

  (b) wrap LLM-output `print(...)` calls with `pretty_print(...)` so every
      lab uses the shared styled output box, not raw Python print.

Targets these print patterns:
    print(<expr>.choices[0].message.content[.strip()])
    print(<expr>.content)
    print("Label:", <expr>.content)
    print("Label:", <expr>.choices[0].message.content)
    print(f"...: {<expr>.content}")
    print(f"...: {<expr>.choices[0].message.content}")

For the labelled forms ("Label:", X) the label becomes the pretty_print title
so the visual emphasis is preserved.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# --- v0 → v1 SDK rewrites (same set used in ChatGPT_API_Tutorial earlier) ---
V0_PATTERNS = [
    (r"openai\.ChatCompletion\.create", "client.chat.completions.create"),
    (r"openai\.Embedding\.create",      "client.embeddings.create"),
    (r"openai\.Image\.create",          "client.images.generate"),
    (r"openai\.api_key\s*=\s*[^\n]+",   "# (api key handled by get_openai_key() in setup cell)"),
    (r"response\['choices'\]\[0\]\['message'\]\['content'\]", "response.choices[0].message.content"),
    (r'response\["choices"\]\[0\]\["message"\]\["content"\]', "response.choices[0].message.content"),
    (r"response\['data'\]", "response.data"),
    (r'response\["data"\]', "response.data"),
    (r"item\['url'\]", "item.url"),
    (r'item\["url"\]', "item.url"),
    (r"emb\['embedding'\]", "emb.embedding"),
    (r'emb\["embedding"\]', "emb.embedding"),
    (r"item\['b64_json'\]", "item.b64_json"),
    (r'item\["b64_json"\]', "item.b64_json"),
]


def _ensure_v1_client(src: str) -> str:
    """If we used `client.X` but never declared it, prepend an init."""
    if "client.chat.completions" in src or "client.embeddings" in src or "client.images" in src:
        if "from openai import OpenAI" not in src and "OpenAI()" not in src:
            return "from openai import OpenAI\nclient = OpenAI()\n\n" + src
    return src


# --- pretty_print wrapping ---
# Match the `expr` in `print(...)`. We accept a small set of well-known LLM
# response shapes and rewrite them.
EXPR = r"[A-Za-z_][\w\.]*"

WRAP_PATTERNS = [
    # print(EXPR.choices[0].message.content[.strip()])
    (
        re.compile(rf"\bprint\((?P<e>{EXPR})\.choices\[0\]\.message\.content(?P<tail>\.strip\(\))?\)"),
        r'pretty_print(\g<e>.choices[0].message.content\g<tail>, title="🤖 Model Response")',
    ),
    # print(EXPR.content)
    (
        re.compile(rf"\bprint\((?P<e>{EXPR})\.content\)"),
        r'pretty_print(\g<e>.content, title="🤖 Model Response")',
    ),
    # print("Label:", EXPR.choices[0].message.content[.strip()])
    (
        re.compile(rf'\bprint\("(?P<t>[^"]+)",\s*(?P<e>{EXPR})\.choices\[0\]\.message\.content(?P<tail>\.strip\(\))?\)'),
        r'pretty_print(\g<e>.choices[0].message.content\g<tail>, title="\g<t>")',
    ),
    # print("Label:", EXPR.content)
    (
        re.compile(rf'\bprint\("(?P<t>[^"]+)",\s*(?P<e>{EXPR})\.content\)'),
        r'pretty_print(\g<e>.content, title="\g<t>")',
    ),
    # print(f"Label: {EXPR.content}")
    (
        re.compile(rf'\bprint\(f"(?P<t>[^"{{}}]+):\s*\{{(?P<e>{EXPR})\.content\}}"\)'),
        r'pretty_print(\g<e>.content, title="\g<t>")',
    ),
]


def transform(src: str) -> tuple[str, dict]:
    notes = {"v0_subs": 0, "wraps": 0}
    new = src
    for pat, repl in V0_PATTERNS:
        new, n = re.subn(pat, repl, new)
        notes["v0_subs"] += n
    new = _ensure_v1_client(new)
    for pat, repl in WRAP_PATTERNS:
        new, n = pat.subn(repl, new)
        notes["wraps"] += n
    return new, notes


def run(path: Path) -> dict:
    nb = json.loads(path.read_text(encoding="utf-8"))
    summary = {"path": str(path), "v0_subs": 0, "wraps": 0, "cells_touched": 0}
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        new, notes = transform(src)
        if new != src:
            cell["source"] = new.splitlines(keepends=True)
            summary["cells_touched"] += 1
            summary["v0_subs"] += notes["v0_subs"]
            summary["wraps"] += notes["wraps"]
    if summary["cells_touched"]:
        path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(Path(".").glob("*.ipynb"))
    for p in paths:
        s = run(Path(p))
        if s["v0_subs"] or s["wraps"]:
            print(json.dumps(s, ensure_ascii=False))
        else:
            print(f"-- no changes: {p}")
