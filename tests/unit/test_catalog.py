"""اختبارات الكتالوج."""

import pytest

from pipeline import catalog
from pipeline.errors import UNITS_MISSING, PipelineError


def test_list_modules_from_excel():
    modules = catalog.list_modules()
    ids = {m.module_id for m in modules}
    assert 1 in ids and 3 in ids
    assert all(m.active for m in modules)


def test_module_3_has_six_units():
    units = catalog.get_units(3)
    assert len(units) == 6
    assert {u.unit_id for u in units} == {7, 9, 10, 11, 13, 14}


def test_module_3_category_243_sub_216():
    subs = catalog.list_subcategories(3, 243)
    assert any(s.sub_category_id == 216 and s.name_ar == "فواكه" for s in subs)
    sub = catalog.get_subcategory(3, 243, 216)
    assert sub.output_slug == "foakh216"


def test_module_1_fruit_categories():
    categories = catalog.list_categories(1)
    ids = {c.category_id for c in categories}
    assert ids == {252, 253, 254, 255}


def test_require_units_raises_when_empty(monkeypatch, tmp_path):
    cat = tmp_path / "catalog"
    cat.mkdir()
    monkeypatch.setattr(catalog, "CATALOG_DIR", cat)
    monkeypatch.setattr(catalog, "MODULES_XLSX", cat / "modules.xlsx")
    monkeypatch.setattr(catalog, "UNITS_XLSX", cat / "units.xlsx")
    catalog.clear_cache()

    with pytest.raises(PipelineError) as exc:
        catalog.require_units(99)
    assert exc.value.code == UNITS_MISSING
    assert "units.xlsx" in str(exc.value)
