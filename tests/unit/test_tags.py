"""اختبارات توليد Tags."""

from pipeline.tags import build_search_tags


def test_tags_include_product_category_and_english_variants():
    tags = build_search_tags(
        product_name="Lay's Chips 150g - 1 Piece",
        category_name="سناكس و شيكولاته",
        subcategory_name="بطاطس و مقبلات",
    )
    parts = [part.strip() for part in tags.split(",")]

    assert "Lay's Chips 150g - 1 Piece" in parts
    assert "Lay's Chips" in parts
    assert "lay's chips" in parts
    assert "lays chips" in parts or "Lays Chips" in parts
    assert "سناكس و شيكولاته" in parts
    assert "بطاطس و مقبلات" in parts
    assert any("سناكس" in part for part in parts)
    assert any("Lay's Chips" in part or "بطاطس و مقبلات Lay's Chips" in part for part in parts)


def test_tags_keep_source_category_when_different():
    tags = build_search_tags(
        product_name="Pepsi 330ml",
        category_name="المشروبات",
        subcategory_name="مشروبات غازيه",
        source_category="Soft Drinks",
    )
    parts = [part.strip() for part in tags.split(",")]

    assert "Pepsi 330ml" in parts
    assert "Soft Drinks" in parts
    assert "المشروبات" in parts
    assert "مشروبات غازيه" in parts


def test_tags_generate_token_combinations():
    tags = build_search_tags(
        product_name="Red Bull Energy Drink",
        category_name="المشروبات",
        subcategory_name="مشروبات الطاقة",
    )
    parts = [part.strip() for part in tags.split(",")]

    assert "Red Bull" in parts
    assert "Energy Drink" in parts
    assert "red bull energy drink" in parts
    assert "Red" in parts
    assert "Bull" in parts
    assert "Energy" in parts
    assert "Drink" in parts


def test_tags_split_arabic_product_name_into_words():
    tags = build_search_tags(
        product_name="تفاح أحمر عماني",
        category_name="فواكه",
        subcategory_name="تفاح",
    )
    parts = [part.strip() for part in tags.split(",")]

    assert "تفاح أحمر عماني" in parts
    assert "تفاح" in parts
    assert "أحمر" in parts
    assert "عماني" in parts
    assert "التفاح" in parts
    assert "الأحمر" in parts
    assert "العماني" in parts
