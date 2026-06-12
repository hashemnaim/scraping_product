"""Vercel ASGI entrypoint for the Streamlit UI."""

from streamlit.starlette import App

app = App("app/ui.py")
