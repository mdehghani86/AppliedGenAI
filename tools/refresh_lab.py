"""
Helper: apply the 2026-05 refresh transforms to a single notebook.

Transforms:
  1. Replace/insert standard header markdown cell at index 0.
  2. Replace/insert "shared utils + key" setup cell at index 1.
  3. Drop any local `def pretty_print(...)` cell (now in utils.py).
  4. Replace outdated model strings with DEFAULT_* constants from utils.
  5. Migrate deprecated LangChain import paths to current ones.

Usage:
    python tools/refresh_lab.py <notebook.ipynb> "<Lab Title>" "<Subtitle>"
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HEADER_MARKER = "applied-genai-header"
SETUP_MARKER = "applied-genai-setup"


def header_cell(title: str, subtitle: str) -> dict:
    src = f"""<!-- {HEADER_MARKER} -->
<div style="background: linear-gradient(135deg, #1e4b8f 0%, #2d6cb8 100%); color: white; padding: 24px; border-radius: 12px; font-family: 'Segoe UI', sans-serif; margin-bottom: 16px;">
  <div style="font-size: 12px; opacity: 0.85; letter-spacing: 1.5px; text-transform: uppercase;">Applied Generative AI · IE 5373</div>
  <h1 style="margin: 8px 0 4px 0; font-size: 28px; font-weight: 600;">{title}</h1>
  <div style="font-size: 14px; opacity: 0.9;">{subtitle}</div>
  <div style="margin-top: 12px; font-size: 12px; opacity: 0.8;">Prof. Mohammad Dehghani · Northeastern University</div>
</div>

> **📌 Note on models.** This lab references specific LLM versions (e.g. `gpt-5`, `gpt-5-mini`).
> Models update quickly — you are welcome (and encouraged) to swap in any newer OpenAI / Anthropic / Google model you have access to.
> The default model is set in one place: `DEFAULT_CHAT_MODEL` inside `utils.py`. Change it there and every cell follows.
"""
    return {
        "cell_type": "markdown",
        "metadata": {"id": HEADER_MARKER},
        "source": src.splitlines(keepends=True),
    }


def setup_cell(lab_title: str) -> dict:
    src = f"""# === Shared lab setup: utils.py + API key + sticky lab pill ===
# Downloads the shared utilities (pretty_print, model constants, key loader,
# lab_pill) from the AppliedGenAI repo so every notebook stays small and
# consistent. The API key is read from a Colab secret named OPENAI_API_KEY
# (set it once under Colab → 🔑 → "Notebook access" — same name in every lab).
import os
if not os.path.exists("utils.py"):
    !wget -q https://raw.githubusercontent.com/mdehghani86/AppliedGenAI/main/utils.py -O utils.py

from utils import (
    pretty_print,
    DEFAULT_CHAT_MODEL,   # e.g. "gpt-5"  — main reasoning model
    DEFAULT_MINI_MODEL,   # e.g. "gpt-5-mini"  — cheaper / faster default
    DEFAULT_EMBED_MODEL,  # e.g. "text-embedding-3-small"
    get_openai_key,
    lab_pill,
)

lab_pill({lab_title!r})        # sticky banner so you always see which lab you're in
get_openai_key(verify=True)    # loads the key + pings OpenAI to confirm it works
"""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"id": SETUP_MARKER},
        "outputs": [],
        "source": src.splitlines(keepends=True),
    }


# Older model strings -> placeholder we substitute. We replace literal quoted
# model strings only, to avoid mangling prose.
MODEL_MAP = {
    '"gpt-3.5-turbo"': 'DEFAULT_MINI_MODEL',
    "'gpt-3.5-turbo'": 'DEFAULT_MINI_MODEL',
    '"gpt-4-1106-preview"': 'DEFAULT_CHAT_MODEL',
    "'gpt-4-1106-preview'": 'DEFAULT_CHAT_MODEL',
    '"gpt-4-turbo"': 'DEFAULT_CHAT_MODEL',
    "'gpt-4-turbo'": 'DEFAULT_CHAT_MODEL',
    '"gpt-4o-mini"': 'DEFAULT_MINI_MODEL',
    "'gpt-4o-mini'": 'DEFAULT_MINI_MODEL',
    '"gpt-4o"': 'DEFAULT_CHAT_MODEL',
    "'gpt-4o'": 'DEFAULT_CHAT_MODEL',
    '"gpt-4"': 'DEFAULT_CHAT_MODEL',
    "'gpt-4'": 'DEFAULT_CHAT_MODEL',
    '"text-embedding-ada-002"': 'DEFAULT_EMBED_MODEL',
    "'text-embedding-ada-002'": 'DEFAULT_EMBED_MODEL',
    '"text-embedding-3-small"': 'DEFAULT_EMBED_MODEL',
}

# LangChain post-1.0 import migration (left = old, right = new).
LC_IMPORT_MAP = [
    ("from langchain.agents.agent_toolkits import", "from langchain_community.agent_toolkits import"),
    ("from langchain.agents import", "from langchain_classic.agents import"),
    ("from langchain.memory import", "from langchain_classic.memory import"),
    ("from langchain.chains.mapreduce import", "from langchain_classic.chains.mapreduce import"),
    ("from langchain.chains.summarize import", "from langchain_classic.chains.summarize import"),
    ("from langchain.chains.combine_documents import", "from langchain_classic.chains.combine_documents import"),
    ("from langchain.chains import", "from langchain_classic.chains import"),
    ("from langchain.prompts import", "from langchain_core.prompts import"),
    ("from langchain.tools import", "from langchain_core.tools import"),
    ("from langchain.chat_models import ChatOpenAI", "from langchain_openai import ChatOpenAI"),
    ("from langchain.chat_models import", "from langchain_openai import"),
    ("from langchain.schema import", "from langchain_core.messages import"),
    ("from langchain.document_loaders import", "from langchain_community.document_loaders import"),
    ("from langchain.text_splitter import", "from langchain_text_splitters import"),
    ("from langchain.docstore.document import", "from langchain_core.documents import"),
    ("from langchain.vectorstores import", "from langchain_community.vectorstores import"),
    ("from langchain.embeddings import", "from langchain_openai import"),
    ("from langchain.utilities import", "from langchain_community.utilities import"),
]

PRETTY_PRINT_RE = re.compile(r"^\s*def\s+pretty_print\s*\(", re.MULTILINE)


def strip_pretty_print(src: str) -> tuple[str, bool]:
    """Remove a top-level `def pretty_print(...)` block from a cell, plus any
    immediately preceding banner/comment lines, plus a trailing print confirmation
    like `print("🎨 Pretty print utility ready!")`. Returns (new_src, removed?).
    """
    lines = src.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    removed = False
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\s*def\s+pretty_print\s*\(", line):
            removed = True
            # Drop preceding banner/comment lines (contiguous, until blank or code)
            while out and (out[-1].lstrip().startswith("#") or out[-1].strip() == ""):
                out.pop()
            # Determine indent of the def
            indent = len(line) - len(line.lstrip())
            i += 1  # skip the def line
            # Skip body: any line that's blank, or indented deeper than `indent`
            while i < len(lines):
                ln = lines[i]
                if ln.strip() == "":
                    i += 1
                    continue
                ln_indent = len(ln) - len(ln.lstrip())
                if ln_indent > indent:
                    i += 1
                    continue
                break
            # Skip a follow-up `print("...pretty print...")` confirmation, if any.
            while i < len(lines):
                ln = lines[i]
                if ln.strip() == "":
                    i += 1
                    continue
                if re.match(r"^\s*print\(.*pretty[ _]print", ln, re.IGNORECASE):
                    i += 1
                    continue
                break
            continue
        out.append(line)
        i += 1
    new_src = "".join(out)
    # Collapse 3+ consecutive blank lines down to 2.
    new_src = re.sub(r"\n{4,}", "\n\n\n", new_src)
    return new_src, removed


def transform_source(src: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    out = src

    for old, new in MODEL_MAP.items():
        # Match `model="gpt-4"` and `model_name="gpt-4"` style assignments
        # by replacing the quoted string only.
        if old in out:
            out = out.replace(old, new)
            notes.append(f"model {old} → {new}")

    for old, new in LC_IMPORT_MAP:
        if old in out:
            out = out.replace(old, new)
            notes.append(f"import: {old.strip()} → {new.strip()}")

    # Migrate `model_name=` kwarg to `model=` for ChatOpenAI (post-langchain 1.0
    # both work but `model` is the documented one).
    if "model_name=" in out and "ChatOpenAI" in out:
        out = re.sub(r"\bmodel_name\s*=", "model=", out)
        notes.append("kwarg: model_name= → model=")

    return out, notes


def refresh(path: Path, title: str, subtitle: str) -> dict:
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = nb["cells"]
    summary = {"path": str(path), "actions": [], "model_changes": 0, "lc_changes": 0,
               "removed_pretty_print": False}

    # 1. Header replace/insert.
    new_header = header_cell(title, subtitle)
    if cells and cells[0].get("metadata", {}).get("id") == HEADER_MARKER:
        cells[0] = new_header
        summary["actions"].append("header replaced")
    else:
        cells.insert(0, new_header)
        summary["actions"].append("header inserted")

    # 2. Setup cell replace/insert at index 1.
    new_setup = setup_cell(title)
    if len(cells) > 1 and cells[1].get("metadata", {}).get("id") == SETUP_MARKER:
        cells[1] = new_setup
        summary["actions"].append("setup cell replaced")
    else:
        cells.insert(1, new_setup)
        summary["actions"].append("setup cell inserted")

    # 3. Remove duplicate pretty_print + model substitutions across remaining cells.
    kept = []
    for cell in cells:
        if cell["cell_type"] != "code":
            kept.append(cell)
            continue
        # Don't re-process our own generated setup cell.
        if cell.get("metadata", {}).get("id") == SETUP_MARKER:
            kept.append(cell)
            continue
        src = "".join(cell["source"])
        if PRETTY_PRINT_RE.search(src) and "from utils import" not in src:
            stripped, did = strip_pretty_print(src)
            if did:
                summary["removed_pretty_print"] = True
                summary["actions"].append("stripped local pretty_print def")
                src = stripped
            # If after stripping the cell is empty, drop it entirely.
            if src.strip() == "":
                continue
        new_src, notes = transform_source(src)
        for n in notes:
            if n.startswith("model"):
                summary["model_changes"] += 1
            elif n.startswith("import") or n.startswith("kwarg"):
                summary["lc_changes"] += 1
        if new_src != src:
            cell["source"] = new_src.splitlines(keepends=True)
        kept.append(cell)

    nb["cells"] = kept
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("usage: refresh_lab.py <notebook.ipynb> <title> <subtitle>")
        sys.exit(1)
    s = refresh(Path(sys.argv[1]), sys.argv[2], sys.argv[3])
    print(json.dumps(s, indent=2, ensure_ascii=False))
