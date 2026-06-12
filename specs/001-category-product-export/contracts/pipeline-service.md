# Pipeline Service Contract

واجهة برمجية داخلية (Python) تستدعيها CLI وStreamlit. ليست REST API في المرحلة الأولى.

## `pipeline.run_category_job(request: CategoryRunRequest) -> CategoryRunResult`

**Input**: يطابق `category-run.schema.json`

**Output**:

```json
{
  "status": "completed",
  "run_key": "2/253/10",
  "id_range": { "start": 86, "end": 170 },
  "excel_path": "output/fruits/fruits.xlsx",
  "images_dir": "output/fruits/fruits_images",
  "stats": {
    "products_total": 85,
    "images_ok": 83,
    "images_failed": 2,
    "bytes_saved": 1240000
  },
  "errors": []
}
```

**Errors** (ترمي `PipelineError`):

| Code | When |
|------|------|
| `UNITS_MISSING` | لا وحدات للموديل في `units.xlsx` |
| `CATALOG_INVALID` | تصنيف غير موجود في الكتالوج |
| `SCRAPE_FAILED` | فشل المصدر بالكامل |
| `STATE_CORRUPT` | `global_state.json` غير صالح |

---

## `catalog.list_modules() -> Module[]`

يعيد الموديلات حيث `active === true` فقط (1–6).

## `catalog.list_categories(module_id) -> Category[]`

## `catalog.list_subcategories(module_id, category_id) -> SubCategory[]`

## `catalog.get_units(module_id) -> Unit[]`

## `id_state.allocate(run_key, count, rescrape: bool) -> IdRange`

- `rescrape=false`: ids جديدة من `last_used_id + 1` أو خطأ إن التصنيف موجود.
- `rescrape=true`: ids من `id_start` المسجّل.

## `images.filter_by_excel(excel_path, images_dir, backup_dir) -> FilterResult`

```json
{
  "kept": 28,
  "removed": 57,
  "missing": ["fruits_images/product_015.webp"],
  "backup_dir": "fruits_images_removed"
}
```

---

## Events (للواجهة — callbacks)

| Event | Payload |
|-------|---------|
| `on_progress` | `{ phase, current, total, message }` |
| `on_product` | `{ id, name, image_ok }` |
| `on_complete` | `CategoryRunResult` |
