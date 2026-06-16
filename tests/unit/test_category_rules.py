"""اختبارات قواعد ربط تصنيف الموقع."""

from pipeline.catalog import CategoryMappingRule
from pipeline.category_rules import resolve_subcategory


def _rules():
    return [
        CategoryMappingRule(3, "مياه", 12, priority=10, active=True),
        CategoryMappingRule(3, "مياه معدنية", 12, priority=30, active=True),
        CategoryMappingRule(3, "مشروبات", 15, priority=5, active=True),
    ]


def test_resolve_subcategory_contains_match():
    sub_id, applied, conflict = resolve_subcategory("مياه معدنية نقية", 99, _rules())
    assert sub_id == 12
    assert applied is True
    assert conflict is False


def test_resolve_subcategory_fallback_default():
    sub_id, applied, conflict = resolve_subcategory("حلويات", 99, _rules())
    assert sub_id == 99
    assert applied is False
    assert conflict is False


def test_resolve_subcategory_empty_source_uses_default():
    sub_id, applied, conflict = resolve_subcategory("", 44, _rules())
    assert sub_id == 44
    assert applied is False


def test_resolve_subcategory_conflict():
    rules = [
        CategoryMappingRule(3, "مشروبات", 10, priority=10, active=True),
        CategoryMappingRule(3, "مشروبات طاقة", 11, priority=10, active=True),
    ]
    sub_id, applied, conflict = resolve_subcategory("مشروبات طاقة", 99, rules)
    assert conflict is True
    assert sub_id == 99
    assert applied is False
