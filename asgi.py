"""Vercel ASGI entrypoint for the Streamlit UI."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from streamlit.starlette import App

_UI_SCRIPT = _ROOT / "app" / "ui.py"

app = App(_UI_SCRIPT)
