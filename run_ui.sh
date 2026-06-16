#!/usr/bin/env bash
cd "$(dirname "$0")"
export PYTHONPATH="${PWD}:${PYTHONPATH}"
PYTHON="${PWD}/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON=python3
fi
exec "$PYTHON" desktop_launcher.py "$@"
