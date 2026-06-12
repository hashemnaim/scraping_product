#!/usr/bin/env bash
cd "$(dirname "$0")"
export PYTHONPATH="${PWD}:${PYTHONPATH}"
exec .venv/bin/streamlit run app/ui.py "$@"
