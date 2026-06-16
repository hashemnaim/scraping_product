"""اختبارات تحميل قواعد ربط التصنيف من الكتالوج."""

from pathlib import Path

import openpyxl

from pipeline import catalog


def test_load_category_mapping_rules_from_xlsx(tmp_path, monkeypatch):
    xlsx = tmp_path / "category_mapping_rules.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["ModuleId", "Pattern", "SubCategoryId", "Priority", "Active", "MatchMode"])
    ws.append([3, "مياه", 12, 10, 1, "contains"])
    wb.save(xlsx)

    monkeypatch.setattr(catalog, "_catalog_dir", lambda: tmp_path)
    catalog.clear_cache()
    rules = catalog.load_category_mapping_rules(3)
    assert len(rules) == 1
    assert rules[0].pattern == "مياه"
    assert rules[0].sub_category_id == 12
