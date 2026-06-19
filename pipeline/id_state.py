"""إدارة الترقيم العالمي للمعرفات."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pipeline.errors import CATEGORY_EXISTS, PipelineError, STATE_CORRUPT

from pipeline.paths import project_root

STATE_PATH = project_root() / "data" / "global_state.json"


@dataclass
class IdRange:
    start: int
    end: int
    ids: list[int]


@dataclass
class CategoryRange:
    id_start: int
    id_end: int
    product_count: int
    excel_path: str
    images_dir: str
    freed_ids: list[int]


def _empty_state() -> dict:
    return {
        "last_used_id": 0,
        "category_ranges": {},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def load_state() -> dict:
    if not STATE_PATH.exists():
        return _empty_state()
    try:
        with open(STATE_PATH, encoding="utf-8") as file:
            data = json.load(file)
        if "last_used_id" not in data or "category_ranges" not in data:
            raise ValueError("missing keys")
        return data
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        raise PipelineError(STATE_CORRUPT, f"ملف الحالة تالف: {exc}") from exc


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_PATH, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)


def _recalculate_last_used_id(state: dict) -> None:
    max_end = 0
    for raw in state.get("category_ranges", {}).values():
        max_end = max(max_end, int(raw.get("id_end", 0)))
    state["last_used_id"] = max_end


def clear_category(run_key: str) -> bool:
    """إزالة تسجيل تصنيف ليبدأ السحب التالي من last_used_id + 1 (أو 1 إن لم يبقَ تصنيف)."""
    state = load_state()
    ranges: dict = state.setdefault("category_ranges", {})
    if run_key not in ranges:
        return False
    del ranges[run_key]
    _recalculate_last_used_id(state)
    save_state(state)
    return True


def reset_all_ids() -> None:
    """إعادة ضبط كل المعرفات — يبدأ السحب التالي من 1."""
    save_state(_empty_state())


def allocate(
    run_key: str,
    count: int,
    rescrape: bool,
    excel_path: str,
    images_dir: str,
) -> IdRange:
    if count < 0:
        raise ValueError("count must be non-negative")

    state = load_state()
    ranges: dict = state.setdefault("category_ranges", {})
    existing = ranges.get(run_key)

    if rescrape:
        if not existing:
            raise PipelineError(
                CATEGORY_EXISTS,
                f"لا يوجد سحب سابق للتصنيف {run_key}. أزل خيار إعادة السحب.",
            )
        id_start = int(existing["id_start"])
        id_end = id_start + count - 1 if count else id_start - 1
        ids = list(range(id_start, id_start + count)) if count else []
        freed = []
        old_end = int(existing.get("id_end", id_start - 1))
        if count < int(existing.get("product_count", 0)):
            freed = list(range(id_start + count, old_end + 1))
        ranges[run_key] = {
            "id_start": id_start,
            "id_end": id_end if count else id_start - 1,
            "product_count": count,
            "excel_path": excel_path,
            "images_dir": images_dir,
            "freed_ids": freed,
        }
        if id_end > state["last_used_id"]:
            state["last_used_id"] = id_end
        save_state(state)
        return IdRange(id_start, id_end if count else id_start - 1, ids)

    if existing:
        raise PipelineError(
            CATEGORY_EXISTS,
            f"التصنيف {run_key} مسجّل مسبقاً. استخدم إعادة السحب أو تصنيفاً آخر.",
        )

    id_start = int(state["last_used_id"]) + 1
    if count == 0:
        return IdRange(id_start - 1, id_start - 1, [])

    id_end = id_start + count - 1
    ids = list(range(id_start, id_end + 1))
    ranges[run_key] = {
        "id_start": id_start,
        "id_end": id_end,
        "product_count": count,
        "excel_path": excel_path,
        "images_dir": images_dir,
        "freed_ids": [],
    }
    state["last_used_id"] = id_end
    save_state(state)
    return IdRange(id_start, id_end, ids)


def get_category_range(run_key: str) -> CategoryRange | None:
    state = load_state()
    raw = state.get("category_ranges", {}).get(run_key)
    if not raw:
        return None
    return CategoryRange(
        int(raw["id_start"]),
        int(raw["id_end"]),
        int(raw.get("product_count", 0)),
        raw.get("excel_path", ""),
        raw.get("images_dir", ""),
        list(raw.get("freed_ids", [])),
    )
