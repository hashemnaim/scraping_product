"""تقرير مراجعة جودة ربط الحقول بعد السحب."""

from __future__ import annotations

from pipeline.match_types import FieldEnrichment, WarningFlag


def collect_warnings(
    product: dict,
    enrichment: FieldEnrichment,
) -> list[str]:
    warnings = list(enrichment.warnings)
    if enrichment.unit.confidence == "low" and enrichment.unit.reason in (
        "default_piece",
        "category_forced_piece",
        "no_marker",
    ):
        if WarningFlag.DEFAULT_UNIT.value not in warnings:
            warnings.append(WarningFlag.DEFAULT_UNIT.value)
    if enrichment.unit.reason == "ambiguous_unit":
        if WarningFlag.AMBIGUOUS_UNIT.value not in warnings:
            warnings.append(WarningFlag.AMBIGUOUS_UNIT.value)
    if enrichment.brand.confidence == "none":
        if WarningFlag.MISSING_BRAND.value not in warnings:
            warnings.append(WarningFlag.MISSING_BRAND.value)
    if not str(product.get("price", "")).strip():
        if WarningFlag.MISSING_PRICE.value not in warnings:
            warnings.append(WarningFlag.MISSING_PRICE.value)
    if not product.get("image_ok"):
        if WarningFlag.FAILED_IMAGE.value not in warnings:
            warnings.append(WarningFlag.FAILED_IMAGE.value)
    for flag in enrichment.warnings:
        if flag not in warnings:
            warnings.append(flag)
    return warnings


def build_review_report(
    enrichments: list[FieldEnrichment],
    products: list[dict],
) -> dict:
    counts: dict[str, int] = {}
    items: list[dict] = []

    for enrichment, product in zip(enrichments, products):
        warnings = collect_warnings(product, enrichment)
        enrichment.warnings = warnings
        for flag in warnings:
            counts[flag] = counts.get(flag, 0) + 1
        if not warnings:
            continue
        items.append(
            {
                "product_id": enrichment.product_id,
                "name": enrichment.product_name,
                "warnings": warnings,
                "unit_id": enrichment.unit.unit_id,
                "quantity_unit": enrichment.unit.quantity_unit,
                "brand_id": enrichment.brand.brand_id,
                "details": _format_details(enrichment),
            }
        )

    total = len(enrichments)
    inferred = sum(1 for e in enrichments if e.unit.confidence in ("high", "medium"))
    default_count = counts.get(WarningFlag.DEFAULT_UNIT.value, 0)
    missing_brand = counts.get(WarningFlag.MISSING_BRAND.value, 0)

    return {
        "products_total": total,
        "ready_for_import": total > 0 and not items,
        "counts": counts,
        "mapping_stats": {
            "inferred_pct": round(inferred / total * 100, 1) if total else 0.0,
            "default_pct": round(default_count / total * 100, 1) if total else 0.0,
            "missing_brand_pct": round(missing_brand / total * 100, 1) if total else 0.0,
        },
        "items": items,
    }


def _format_details(enrichment: FieldEnrichment) -> str:
    parts = [f"وحدة: {enrichment.unit.reason} ({enrichment.unit.confidence})"]
    parts.append(f"علامة: {enrichment.brand.reason} ({enrichment.brand.confidence})")
    return " | ".join(parts)
