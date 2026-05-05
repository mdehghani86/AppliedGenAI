"""
Applied Generative AI — shared lab utilities.

Drop this file next to a notebook (or `wget` it inside Colab) and use:

    from utils import pretty_print, DEFAULT_CHAT_MODEL, DEFAULT_MINI_MODEL, DEFAULT_EMBED_MODEL

The Colab one-liner used by every lab in this repo:

    !wget -q https://raw.githubusercontent.com/mdehghani86/AppliedGenAI/main/utils.py -O utils.py

Course: Applied Generative AI (IE 5373) — Prof. Mohammad Dehghani.
"""

from __future__ import annotations

# --- Default model choices ---------------------------------------------------
# We default to the gpt-4o family rather than gpt-5 because every lab in this
# course uses `temperature=` (often 0 for deterministic prompting comparisons),
# and gpt-5 / gpt-5-mini / gpt-5-nano currently only accept the default
# temperature (=1). Sticking with gpt-4o keeps every notebook runnable end to
# end without parameter rewrites.
#
# Want to upgrade to gpt-5 anyway? Change these constants AND remove every
# `temperature=` argument in the lab. Or use `gpt-5-chat-latest`, which is the
# only gpt-5 variant that accepts custom temperature.
DEFAULT_CHAT_MODEL = "gpt-4o"
DEFAULT_MINI_MODEL = "gpt-4o-mini"
DEFAULT_EMBED_MODEL = "text-embedding-3-small"

_THEMES = {
    "blue":   {"color": "#1e4b8f", "background": "#f0f6ff"},
    "red":    {"color": "#c62828", "background": "#ffebee"},
    "yellow": {"color": "#b26a00", "background": "#fff8e1"},
    "green":  {"color": "#1b5e20", "background": "#e8f5e9"},
    "gray":   {"color": "#37474f", "background": "#eceff1"},
}


def pretty_print(text, title="🤖 Model Response", theme="blue", style=None):
    """Display a styled message box in a Jupyter / Colab notebook.

    Backwards compatible with the older lab signatures:
      - pretty_print(text, title)
      - pretty_print(text, title, style="blue")
      - pretty_print(text, title, theme="blue")
    """
    from IPython.display import HTML, display

    chosen = (style or theme or "blue").lower()
    palette = _THEMES.get(chosen, _THEMES["blue"])
    body = str(text).replace("\n", "<br>")

    display(HTML(f"""
    <div style="border-left: 5px solid {palette['color']};
                padding: 12px 16px;
                background-color: {palette['background']};
                border-radius: 6px;
                font-family: 'Segoe UI', sans-serif;
                line-height: 1.6;
                margin: 10px 0;">
        <strong style="color: {palette['color']}; font-size: 16px;">{title}</strong><br>
        <span style="font-size: 14px; color: #333;">{body}</span>
    </div>
    """))


def get_openai_key(verify: bool = True):
    """Resolve the OpenAI API key from Colab secrets, then env, then prompt.

    All labs in this course use the SAME secret name: `OPENAI_API_KEY`.
    Set it once under Colab → 🔑 → "Notebook access" and every lab picks it up.

    If `verify=True`, makes a tiny `client.models.list()` call and prints a
    green ✅ on success or a red ❌ with the error otherwise.
    """
    import os
    source = None
    key = None
    try:
        from google.colab import userdata
        key = userdata.get("OPENAI_API_KEY")
        if key:
            source = "Colab secret"
    except Exception:
        pass
    if not key:
        key = os.environ.get("OPENAI_API_KEY")
        if key:
            source = "environment variable"
    if not key:
        from getpass import getpass
        key = getpass("Enter your OPENAI_API_KEY: ").strip()
        source = "manual entry"
    os.environ["OPENAI_API_KEY"] = key

    if verify:
        verify_openai_key(source=source)
    return key


def verify_openai_key(source: str | None = None) -> bool:
    """Ping the OpenAI API to confirm the configured key works."""
    from IPython.display import HTML, display
    try:
        from openai import OpenAI
        OpenAI().models.list()
        display(HTML(
            f"<div style='padding:8px 12px;background:#e8f5e9;border-left:4px solid #1b5e20;"
            f"border-radius:4px;font-family:Segoe UI,sans-serif;font-size:13px;'>"
            f"✅ <b>OpenAI API key works.</b>" + (f" Source: <i>{source}</i>." if source else "") +
            f"</div>"))
        return True
    except Exception as e:
        display(HTML(
            f"<div style='padding:8px 12px;background:#ffebee;border-left:4px solid #c62828;"
            f"border-radius:4px;font-family:Segoe UI,sans-serif;font-size:13px;'>"
            f"❌ <b>OpenAI API key check failed.</b><br>"
            f"<code>{type(e).__name__}: {e}</code><br>"
            f"In Colab: open the 🔑 sidebar, add a secret named "
            f"<code>OPENAI_API_KEY</code>, and toggle <i>Notebook access</i> ON."
            f"</div>"))
        return False


def lab_pill(title: str, color: str = "#1e4b8f") -> None:
    """Render a sticky pill at the top of the notebook so the lab name stays
    visible as the student scrolls. Uses CSS position:sticky which works in
    Colab and JupyterLab."""
    from IPython.display import HTML, display
    display(HTML(f"""
    <div style="position: sticky; top: 0; z-index: 9999; text-align: center;
                padding: 6px 0; pointer-events: none;">
      <span style="display: inline-block; background: {color}; color: white;
                   padding: 6px 16px; border-radius: 999px;
                   font-family: 'Segoe UI', sans-serif; font-size: 12px;
                   font-weight: 600; letter-spacing: 0.5px;
                   box-shadow: 0 2px 6px rgba(0,0,0,0.15);">
        📘 {title}
      </span>
    </div>
    """))
