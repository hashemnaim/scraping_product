"""اختبارات توثيق مصادر الحقول."""

from pipeline.field_mapping import (
    CRITICAL_FIELDS,
    FIELD_SOURCES,
    WORKFLOW_TIP,
    build_pre_scrape_summary,
    field_source_rows,
)


def test_critical_fields_have_sources():
    for field in CRITICAL_FIELDS:
        assert field in FIELD_SOURCES
        assert FIELD_SOURCES[field]["source_ar"]


def test_field_source_rows_cover_critical_and_scraped():
    rows = field_source_rows()
    fields = {row["field"] for row in rows}
    assert "CategoryId" in fields
    assert "UnitId" in fields
    assert "Name" in fields


def test_build_pre_scrape_summary():
    summary = build_pre_scrape_summary(3, 12, 45, "خضروات", "فواكه", 6)
    assert summary["module_id"] == 3
    assert summary["sub_category_id"] == 45
    assert summary["workflow_tip"] == WORKFLOW_TIP
    assert len(summary["fields"]) >= 5
