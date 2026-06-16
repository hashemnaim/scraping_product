"""سجل تشغيل عمليات السحب."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pipeline.paths import project_root


def run_history_path() -> Path:
    return project_root() / "data" / "run_history.jsonl"


def append_run_log(entry: dict) -> None:
    path = run_history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **entry,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
