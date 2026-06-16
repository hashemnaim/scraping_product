"""اختبارات مطابقة الوحدات — القطعة أولاً."""

from pipeline.catalog import Unit
from pipeline.units_matcher import (
    finalize_unit_for_export,
    match_unit,
    match_unit_for_category,
    match_unit_with_meta,
)


def _module3_units() -> list[Unit]:
    return [
        Unit(3, 7, "قطعه", ["piece", "pieces", "pc", "pcs", "قطعة", "حبة", "بالقطعة"]),
        Unit(3, 9, "كيلو", ["kg", "kilo", "kilogram", "كجم", "كيلو"]),
        Unit(3, 10, "غرام", ["g", "gram", "grams", "gr", "جم", "غرام"]),
        Unit(3, 11, "فرط", ["فرط", "bunch"]),
        Unit(3, 13, "حزمة", ["حزمة", "pack", "bundle"]),
        Unit(3, 14, "ml", ["ml", "مل", "milliliter", "millilitre"]),
    ]


def test_piece_wins_over_weight():
    units = _module3_units()
    unit_id, quantity = match_unit("Chips 150g - 1 Piece", units)
    assert unit_id == 7
    assert quantity == "1"


def test_piece_with_ml_and_count():
    units = _module3_units()
    unit_id, quantity = match_unit("Water 500ml - 2 Piece", units)
    assert unit_id == 7
    assert quantity == "2"


def test_kilogram_only():
    units = _module3_units()
    unit_id, quantity = match_unit("Tomato 1 kg", units)
    assert unit_id == 9
    assert quantity == "1"


def test_gram_only():
    units = _module3_units()
    unit_id, quantity = match_unit("Cheese 250 g", units)
    assert unit_id == 10
    assert quantity == "250"


def test_ml_only():
    units = _module3_units()
    unit_id, quantity = match_unit("Juice 500ml", units)
    assert unit_id == 14
    assert quantity == "500"


def test_arabic_piece():
    units = _module3_units()
    unit_id, quantity = match_unit("شيبس 150g - 2 قطعة", units)
    assert unit_id == 7
    assert quantity == "2"


def test_bilqitaa_without_number():
    units = _module3_units()
    unit_id, quantity = match_unit("منتج بالقطعة", units)
    assert unit_id == 7
    assert quantity == "1"


def test_no_unit_marker():
    units = _module3_units()
    unit_id, quantity = match_unit("Product without unit", units)
    assert unit_id is None
    assert quantity is None


def test_exception_category_keeps_kilogram():
    units = _module3_units()
    unit_id, quantity = match_unit_for_category(
        "Tomato 1 kg",
        units,
        category_name="الفواكه والخضروات",
        subcategory_name="فواكه",
    )
    assert unit_id == 9
    assert quantity == "1"


def test_exception_category_keeps_gram():
    units = _module3_units()
    unit_id, quantity = match_unit_for_category(
        "Cheese 250 g",
        units,
        category_name="الألبان , البيض والجبنة",
        subcategory_name="الجبنة واللبنة",
    )
    assert unit_id == 10
    assert quantity == "250"


def test_non_exception_weight_becomes_piece():
    units = _module3_units()
    unit_id, quantity = match_unit_for_category(
        "Cheese 250 g",
        units,
        category_name="سناكس و شيكولاته",
        subcategory_name="بطاطس و مقبلات",
    )
    assert unit_id == 7
    assert quantity == "1"


def test_non_exception_ml_becomes_piece():
    units = _module3_units()
    unit_id, quantity = match_unit_for_category(
        "Juice 500ml",
        units,
        category_name="سناكس و شيكولاته",
        subcategory_name="مقبلات",
    )
    assert unit_id == 7
    assert quantity == "1"


def test_non_exception_piece_with_weight_unchanged():
    units = _module3_units()
    unit_id, quantity = match_unit_for_category(
        "Chips 150g - 1 Piece",
        units,
        category_name="سناكس و شيكولاته",
        subcategory_name="مقبلات",
    )
    assert unit_id == 7
    assert quantity == "1"


def test_non_exception_piece_count_unchanged():
    units = _module3_units()
    unit_id, quantity = match_unit_for_category(
        "Water 500ml - 2 Piece",
        units,
        category_name="المشروبات",
        subcategory_name="مشروبات غازيه",
    )
    assert unit_id == 7
    assert quantity == "2"


def test_finalize_ml_becomes_piece():
    units = _module3_units()
    unit_id, quantity = finalize_unit_for_export(14, "500", units)
    assert unit_id == 7
    assert quantity == "1"


def test_finalize_gram_stays():
    units = _module3_units()
    unit_id, quantity = finalize_unit_for_export(10, "250", units)
    assert unit_id == 10
    assert quantity == "250"


def test_finalize_empty_becomes_piece():
    units = _module3_units()
    unit_id, quantity = finalize_unit_for_export(None, None, units)
    assert unit_id == 7
    assert quantity == "1"


def test_finalize_piece_keeps_count():
    units = _module3_units()
    unit_id, quantity = finalize_unit_for_export(7, "2", units)
    assert unit_id == 7
    assert quantity == "2"


def test_match_unit_with_meta_kilogram_high_confidence():
    units = _module3_units()
    result = match_unit_with_meta(
        "طماطم 1 كيلو",
        units,
        category_name="الفواكه والخضروات",
        subcategory_name="خضروات",
    )
    assert result.unit_id == 9
    assert result.quantity_unit == "1"
    assert result.confidence == "high"
    assert result.reason == "pattern_weight"


def test_match_unit_with_meta_ml_forced_piece_low():
    units = _module3_units()
    result = match_unit_with_meta(
        "حليب 500 مل",
        units,
        category_name="سوبرماركت",
        subcategory_name="ألبان",
    )
    assert result.unit_id == 7
    assert result.quantity_unit == "1"
    assert result.confidence == "low"
    assert result.reason == "category_forced_piece"


def test_match_unit_with_meta_default_piece_special_offer():
    units = _module3_units()
    result = match_unit_with_meta(
        "عرض خاص",
        units,
        category_name="سناكس",
        subcategory_name="مقبلات",
    )
    assert result.unit_id == 7
    assert result.confidence == "low"
    assert result.reason in ("default_piece", "no_marker")
