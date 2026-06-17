"""تنسيق عملية سحب تصنيف كامل."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import requests

from pipeline import catalog, exporter, id_state, images
from pipeline.catalog import (
    get_module,
    get_subcategory,
    get_units,
    list_categories,
    load_category_mapping_rules,
    make_run_key,
    require_units,
)
from pipeline.brand_matcher import match_brand_with_meta
from pipeline.category_rules import resolve_subcategory
from pipeline.match_types import FieldEnrichment, WarningFlag
from pipeline.review_report import build_review_report
from pipeline.run_history import append_run_log
from pipeline.tags import build_search_tags
from pipeline.units_matcher import match_unit_with_meta
from pipeline.errors import SCRAPE_FAILED, PipelineError
from pipeline.scrape.detector import scrape_category

from pipeline.paths import project_root

ProgressCallback = Callable[[str, int, int, str], None]


@dataclass
class CategoryRunRequest:
    module_id: int
    category_id: int
    sub_category_id: int
    source_url: str
    output_dir: str = "output"
    excel_filename: str = "products.xlsx"
    images_folder: str = "product_images"
    max_pages: int = 0
    start_page: int = 1
    rescrape: bool = False
    mode: str = "auto"
    apply_category_rules: bool = False


@dataclass
class CategoryRunResult:
    status: str
    run_key: str
    id_range: dict
    excel_path: str
    images_dir: str
    stats: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    review_report: dict = field(default_factory=dict)
    mapping_stats: dict = field(default_factory=dict)


def _default_progress(phase: str, current: int, total: int, message: str):
    pass


def run_category_job(
    request: CategoryRunRequest,
    on_progress: ProgressCallback | None = None,
) -> CategoryRunResult:
    progress = on_progress or _default_progress

    get_module(request.module_id)
    sub = get_subcategory(request.module_id, request.category_id, request.sub_category_id)
    require_units(request.module_id)
    module = get_module(request.module_id)
    module_units = get_units(request.module_id)
    category_name = ""
    for category in list_categories(request.module_id):
        if category.category_id == request.category_id:
            category_name = category.name_ar
            break

    mapping_rules = (
        load_category_mapping_rules(request.module_id)
        if request.apply_category_rules
        else []
    )

    run_key = make_run_key(request.module_id, request.category_id, request.sub_category_id)
    output_base = project_root() / request.output_dir / sub.output_slug
    excel_filename = request.excel_filename or sub.excel_filename
    excel_path = output_base / excel_filename
    images_folder_name = images.images_folder_from_excel(excel_filename)
    images_dir = output_base / images_folder_name
    images_dir.mkdir(parents=True, exist_ok=True)

    if request.rescrape:
        existing = id_state.get_category_range(run_key)
        if existing:
            images.remove_images_in_range(
                images_dir, existing.id_start, existing.id_end
            )

    session = requests.Session()
    progress("scrape", 0, 1, "جاري سحب المنتجات...")
    try:
        raw_products = scrape_category(
            request.source_url,
            session,
            request.max_pages,
            mode=request.mode,
            on_progress=progress,
            start_page=request.start_page,
        )
    except Exception as exc:
        raise PipelineError(SCRAPE_FAILED, str(exc)) from exc

    if not raw_products:
        raise PipelineError(SCRAPE_FAILED, "لم يُعثر على منتجات")

    id_range = id_state.allocate(
        run_key,
        len(raw_products),
        request.rescrape,
        str(excel_path.relative_to(project_root())),
        str(images_dir.relative_to(project_root())),
    )

    images_ok = 0
    images_failed = 0
    bytes_saved = 0
    rows = []
    enrichments: list[FieldEnrichment] = []

    for index, (product_id, product) in enumerate(zip(id_range.ids, raw_products)):
        progress("images", index + 1, len(raw_products), product.get("name", "")[:40])
        image_path = images_dir / images.image_filename(product_id)
        ok, saved = images.download_product_image(
            product.get("image_url", ""), image_path, session
        )
        rel_path = ""
        if ok:
            images_ok += 1
            bytes_saved += saved
            rel_path = images.image_relative_path(images_folder_name, product_id)
            product["image_ok"] = True
        else:
            images_failed += 1
            product["image_ok"] = False

        product["image_path"] = rel_path
        product["tags"] = build_search_tags(
            product_name=product.get("name", ""),
            category_name=category_name,
            subcategory_name=sub.name_ar,
            source_category=product.get("category", ""),
        )

        unit_match = match_unit_with_meta(
            product.get("name", ""),
            module_units,
            category_name=category_name,
            subcategory_name=sub.name_ar,
        )
        brand_match = match_brand_with_meta(product.get("name", ""), request.module_id)

        if unit_match.unit_id is not None:
            product["unit_id"] = unit_match.unit_id
        if unit_match.quantity_unit is not None:
            product["quantity_unit"] = unit_match.quantity_unit
        if brand_match.brand_id is not None:
            product["brand_id"] = brand_match.brand_id

        resolved_sub_id = request.sub_category_id
        rule_warnings: list[str] = []
        if mapping_rules:
            resolved_sub_id, rule_applied, conflict = resolve_subcategory(
                product.get("category", ""),
                request.sub_category_id,
                mapping_rules,
            )
            if rule_applied:
                rule_warnings.append(WarningFlag.CATEGORY_RULE_APPLIED.value)
            if conflict:
                rule_warnings.append(WarningFlag.CATEGORY_RULE_CONFLICT.value)

        enrichments.append(
            FieldEnrichment(
                product_id=product_id,
                product_name=product.get("name", ""),
                unit=unit_match,
                brand=brand_match,
                warnings=rule_warnings,
                source_category=product.get("category", ""),
                resolved_sub_category_id=resolved_sub_id,
            )
        )

        rows.append(
            exporter.build_row(
                product_id,
                product,
                images_folder_name,
                request.module_id,
                request.category_id,
                resolved_sub_id,
                module.import_defaults,
            )
        )

    review_report = build_review_report(enrichments, raw_products)
    mapping_stats = review_report.get("mapping_stats", {})

    exporter.write_excel(rows, excel_path)

    if request.rescrape and id_range.ids:
        keep_ids = set(id_range.ids)
        backup = Path(str(images_dir) + "_removed")
        images.move_orphan_images_to_backup(images_dir, keep_ids, backup)

    append_run_log(
        {
            "run_key": run_key,
            "source_url": request.source_url,
            "module_id": request.module_id,
            "category_id": request.category_id,
            "sub_category_id": request.sub_category_id,
            "apply_category_rules": request.apply_category_rules,
            "products_total": len(raw_products),
            "warning_counts": review_report.get("counts", {}),
            "excel_path": str(excel_path),
        }
    )

    return CategoryRunResult(
        status="completed",
        run_key=run_key,
        id_range={"start": id_range.start, "end": id_range.end},
        excel_path=str(excel_path),
        images_dir=str(images_dir),
        stats={
            "products_total": len(raw_products),
            "images_ok": images_ok,
            "images_failed": images_failed,
            "bytes_saved": bytes_saved,
        },
        review_report=review_report,
        mapping_stats=mapping_stats,
        errors=[],
    )
