"""اختبارات فصل السعة/الحجم/الوزن عن الاسم."""

from pipeline.name_parser import split_name_and_size


def test_split_ml_from_name():
    clean, size = split_name_and_size("Pepsi Extra Caffeine Drink - 355 ml")
    assert clean == "Pepsi Extra Caffeine Drink"
    assert size == "355 ml"


def test_split_pack_and_ml():
    clean, size = split_name_and_size("V Super Soda Cola Soft Drink, 300 ml - Pack of 6")
    assert clean == "V Super Soda Cola Soft Drink"
    assert "300 ml" in size
    assert "Pack of 6" in size


def test_split_liter():
    clean, size = split_name_and_size("Big Lemon Mint - 1.25 Liter")
    assert clean == "Big Lemon Mint"
    assert size == "1.25 Liter"


def test_split_gram():
    clean, size = split_name_and_size("Pico Blackberry - 125 g")
    assert clean == "Pico Blackberry"
    assert size == "125 g"


def test_split_arabic_api_name():
    clean, size = split_name_and_size("في سوبر صودا مشروب غازي كولا، 300 مل - عبوة من 6")
    assert clean == "في سوبر صودا مشروب غازي كولا"
    assert "300 مل" in size
    assert "عبوة من 6" in size


def test_split_arabic_pepsi():
    clean, size = split_name_and_size("بيبسي مشروب اكسترا كافيين - 355 مل")
    assert clean == "بيبسي مشروب اكسترا كافيين"
    assert size == "355 مل"


def test_split_piece_and_weight():
    clean, size = split_name_and_size("Chips 150g - 1 Piece")
    assert clean == "Chips"
    assert "150g" in size
    assert "1 Piece" in size
