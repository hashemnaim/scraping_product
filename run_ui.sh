#!/usr/bin/env bash
cd "$(dirname "$0")"
export PYTHONPATH="${PWD}:${PYTHONPATH}"
PYTHON="${PWD}/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON=python3
fi
"$PYTHON" -c "
from pipeline.scrape.playwright_bootstrap import ensure_playwright_chromium
ensure_playwright_chromium()
" || exit 1
exec "$PYTHON" -m streamlit run app/ui.py "$@"
