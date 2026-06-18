"""اختبارات التعريب."""

from pipeline.arabic_localizer import contains_arabic, localize_product_name
from pipeline.tags import build_search_tags


def test_contains_arabic():
    assert contains_arabic("بيبسي 355 مل")
    assert not contains_arabic("Pepsi 355 ml")


def test_localize_pepsi():
    name = localize_product_name("Pepsi Extra Caffeine Drink - 355 ml")
    assert contains_arabic(name)
    assert "بيبسي" in name
    assert "355 مل" in name


def test_localize_red_bull():
    name = localize_product_name("Red Bull Energy Drink with White Peach - 250 ml")
    assert contains_arabic(name)
    assert "ريد بول" in name
    assert "250 مل" in name


def test_localize_keeps_arabic_name():
    original = "حليب كامل الدسم 1 لتر"
    assert localize_product_name(original) == original


def test_arabic_only_tags_exclude_english():
    tags = build_search_tags(
        product_name="بيبسي إكسترا كافيين مشروب - 355 مل",
        category_name="المشروبات",
        subcategory_name="مشروبات غازيه",
        source_category="Soft Drinks",
        arabic_only=True,
    )
    parts = [part.strip() for part in tags.split(",")]

    assert "بيبسي إكسترا كافيين مشروب - 355 مل" in parts
    assert "المشروبات" in parts
    assert "مشروبات غازيه" in parts
    assert "Soft Drinks" not in parts
    assert all(("\u0600" <= ch <= "\u06ff") for part in parts for ch in part if ch.isalpha())
