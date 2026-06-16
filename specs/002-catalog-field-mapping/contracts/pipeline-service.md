# Pipeline Extension: Field Mapping & Review

**Branch**: `002-catalog-field-mapping` | **Extends**: [001 pipeline-service.md](../001-category-product-export/contracts/pipeline-service.md)

## CategoryRunResult (extended)

```json
{
  "status": "completed",
  "run_key": "3/12/45",
  "excel_path": "output/slug/products.xlsx",
  "images_dir": "output/slug/product_images",
  "stats": {
    "products_total": 120,
    "images_ok": 118,
    "images_failed": 2
  },
  "review_report": {
    "products_total": 120,
    "ready_for_import": false,
    "counts": {
      "default_unit": 8,
      "missing_brand": 15,
      "failed_image": 2
    },
    "mapping_stats": {
      "inferred_pct": 72.5,
      "default_pct": 6.7,
      "missing_brand_pct": 12.5
    },
    "items": []
  }
}
```

## Pre-scrape summary (UI-only)

Not persisted — built from `field_mapping.build_pre_scrape_summary()`.

## Run history append

On successful run, append one JSON line to `data/run_history.jsonl`.
