"""اختبارات الترقيم العالمي."""

import json
from pathlib import Path

import pytest

from pipeline import id_state
from pipeline.errors import CATEGORY_EXISTS, PipelineError


@pytest.fixture
def isolated_state(tmp_path, monkeypatch):
    state_file = tmp_path / "global_state.json"
    monkeypatch.setattr(id_state, "STATE_PATH", state_file)
    return state_file


def test_contiguous_ids_two_categories(isolated_state):
    r1 = id_state.allocate("2/253/10", 3, False, "out/a.xlsx", "out/a_img")
    assert r1.ids == [1, 2, 3]
    assert r1.end == 3

    r2 = id_state.allocate("2/254/11", 2, False, "out/b.xlsx", "out/b_img")
    assert r2.ids == [4, 5]
    assert r2.start == 4

    state = json.loads(isolated_state.read_text())
    assert state["last_used_id"] == 5


def test_rescrape_reuses_id_start(isolated_state):
    id_state.allocate("2/253/10", 5, False, "out/a.xlsx", "out/a_img")
    r = id_state.allocate("2/253/10", 3, True, "out/a.xlsx", "out/a_img")
    assert r.ids == [1, 2, 3]
    assert r.start == 1

    state = json.loads(isolated_state.read_text())
    assert state["category_ranges"]["2/253/10"]["freed_ids"] == [4, 5]


def test_clear_category_resets_to_start_at_one(isolated_state):
    id_state.allocate("2/253/10", 3, False, "out/a.xlsx", "out/a_img")
    assert id_state.clear_category("2/253/10") is True
    r = id_state.allocate("2/253/10", 2, False, "out/a.xlsx", "out/a_img")
    assert r.ids == [1, 2]


def test_new_scrape_blocked_if_exists(isolated_state):
    id_state.allocate("2/253/10", 2, False, "out/a.xlsx", "out/a_img")
    with pytest.raises(PipelineError) as exc:
        id_state.allocate("2/253/10", 2, False, "out/a.xlsx", "out/a_img")
    assert exc.value.code == CATEGORY_EXISTS
