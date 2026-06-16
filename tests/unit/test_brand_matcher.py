"""اختبارات مطابقة العلامات التجارية."""

from pipeline.brand_matcher import load_brands, match_brand


def test_match_brand_arabic_substring():
    assert match_brand("حليب جهينة كامل الدسم 1 لتر", module_id=3) == 5


def test_match_brand_longer_name_first():
    assert match_brand("مشروب بيبسي دايت 330 مل", module_id=3) == 10


def test_match_brand_english_product_name():
    assert match_brand("Pepsi Cola 330ml", module_id=3) == 6


def test_match_brand_diva_english():
    assert match_brand("Diva Antibacterial Moisturizing Liquid Hand Wash", module_id=3) == 437


def test_match_brand_lux_arabic_optional():
    # لوكس غير موجود في brands.csv — لا يُفترض تطابق
    assert match_brand("لوح الصابون حلم السعادة من لوكس", module_id=3) is None


def test_load_brands_filters_module():
    brands = load_brands(3)
    assert brands
    assert all(brand.module_id == 3 for brand in brands)
