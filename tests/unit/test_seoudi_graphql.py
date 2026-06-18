"""اختبارات سعودي GraphQL."""

from pipeline.scrape.seoudi_graphql import _pick_category_by_url_key, parse_seoudi_url


def test_parse_seoudi_soft_drinks_url():
    locale, category_path, start_page = parse_seoudi_url(
        "https://seoudisupermarket.com/ar/beverages/soft-drinks"
    )
    assert locale == "ar"
    assert category_path == "beverages/soft-drinks"
    assert start_page == 1


def test_pick_category_prefers_parent_path_match():
    categories = [
        {
            "url_path": "top-offers/disabled-campaigns/traditional-eid-2026/soft-drinks",
            "url_key": "soft-drinks",
            "products": {"total_count": 70},
        },
        {
            "url_path": "beverages/fresh-juices",
            "url_key": "soft-drinks",
            "products": {"total_count": 396},
        },
    ]
    picked = _pick_category_by_url_key(categories, "beverages/soft-drinks")
    assert picked is not None
    assert picked["url_path"] == "beverages/fresh-juices"
