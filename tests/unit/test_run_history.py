"""اختبارات سجل التشغيل."""

import json

from pipeline.run_history import append_run_log


def test_append_run_log(tmp_path, monkeypatch):
    log_file = tmp_path / "data" / "run_history.jsonl"
    monkeypatch.setattr("pipeline.run_history.run_history_path", lambda: log_file)
    append_run_log({"run_key": "3/1/2", "products_total": 5})
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["run_key"] == "3/1/2"
    assert record["products_total"] == 5
    assert "timestamp" in record
