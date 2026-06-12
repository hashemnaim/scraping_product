"""Vercel ASGI entrypoint for the Streamlit UI."""

from pathlib import Path

from streamlit.starlette import App

_UI_SCRIPT = Path(__file__).resolve().parent.parent / "app" / "ui.py"

app = App(_UI_SCRIPT)
