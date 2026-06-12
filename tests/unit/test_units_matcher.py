"""اختبارات مطابقة الوحدات — القطعة أولاً."""

from pipeline.catalog import Unit
from pipeline.units_matcher import match_unit


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
