#!/usr/bin/env bash
cd "$(dirname "$0")"
export PYTHONPATH="${PWD}:${PYTHONPATH}"
exec python3 desktop_launcher.py "$@"
