"""اختبارات تقرير المراجعة."""

from pipeline.match_types import BrandMatchResult, FieldEnrichment, UnitMatchResult
from pipeline.review_report import build_review_report, collect_warnings


def _enrichment(
    product_id: int,
    name: str,
    unit_reason: str = "default_piece",
    unit_conf: str = "low",
    brand_conf: str = "none",
) -> FieldEnrichment:
    return FieldEnrichment(
        product_id=product_id,
        product_name=name,
        unit=UnitMatchResult(7, "1", unit_conf, unit_reason),
        brand=BrandMatchResult(None, brand_conf, "no_match"),
    )


def test_review_report_counts_warnings():
    enrichments = [
        _enrichment(1, "عرض خاص", unit_reason="default_piece"),
        _enrichment(2, "بيبسي 330 مل", unit_reason="pattern_volume", unit_conf="high", brand_conf="high"),
    ]
    products = [
        {"name": "عرض خاص", "price": "10", "image_ok": True},
        {"name": "بيبسي", "price": "", "image_ok": False},
    ]
    report = build_review_report(enrichments, products)
    assert report["products_total"] == 2
    assert report["counts"].get("default_unit", 0) >= 1
    assert report["counts"].get("missing_brand", 0) >= 1
    assert report["counts"].get("failed_image", 0) == 1
    assert report["ready_for_import"] is False


def test_review_report_ready_when_clean():
    enrichment = FieldEnrichment(
        product_id=1,
        product_name="طماطم 1 كيلو",
        unit=UnitMatchResult(9, "1", "high", "pattern_weight"),
        brand=BrandMatchResult(5, "high", "substring"),
    )
    products = [{"name": "طماطم", "price": "20", "image_ok": True}]
    report = build_review_report([enrichment], products)
    assert report["ready_for_import"] is True
    assert report["items"] == []


def test_collect_warnings_missing_price():
    enrichment = _enrichment(1, "test", unit_conf="high", unit_reason="pattern_weight")
    warnings = collect_warnings({"price": "", "image_ok": True}, enrichment)
    assert "missing_price" in warnings
