# Data Model: نظام تصدير المنتجات تصنيفاً بتصنيف

**Branch**: `001-category-product-export` | **Date**: 2026-06-09

## Entity Relationship Overview

```text
Module (1–8)
  ├── Category (CategoryId)
  │     └── SubCategory (SubCategoryId)
  ├── Unit[] (per module, from units.xlsx)
  └── ModuleDefaults (stock, status, …)

CategoryRun
  ├── references Module + Category + SubCategory
  ├── source_url, scraper profile
  └── produces ProductRow[] + ProductImage[]

GlobalIdState
  ├── last_used_id
  └── category_ranges: { run_key → { id_start, id_end, output_path } }

ProductRow → 29 Excel columns
ProductImage → WebP file named by ProductRow.Id
```

---

## Module

| Field | Type | Rules |
|-------|------|-------|
| `module_id` | int | 1–6 active; 7–8 reserved (`active: false`) |
| `name_ar` | string | اسم عرض في الواجهة |
| `active` | bool | false لـ 7–8 حتى التفعيل |

**Relationships**: one Module → many Categories, many Units.

---

## Category

| Field | Type | Rules |
|-------|------|-------|
| `category_id` | int | فريد ضمن نظام الاستيراد |
| `module_id` | int | FK → Module |
| `name_ar` | string | |
| `subcategories` | SubCategory[] | |

---

## SubCategory

| Field | Type | Rules |
|-------|------|-------|
| `sub_category_id` | int | |
| `category_id` | int | FK → Category |
| `name_ar` | string | |
| `default_source_url` | string? | اختياري — يملأ حقل الرابط في الواجهة |
| `output_slug` | string | اسم مجلد الإخراج (مثل `fruits`) |

**Run key**: `{module_id}/{category_id}/{sub_category_id}` — يُستخدم في `GlobalIdState.category_ranges`.

---

## Unit

| Field | Type | Rules |
|-------|------|-------|
| `module_id` | int | FK → Module |
| `unit_id` | int | معرف الاستيراد |
| `name_ar` | string | |
| `aliases` | string[] | للمطابقة من اسم المنتج (kg, g, …) |

**Validation**: `unit_id` فريد ضمن `module_id`؛ لا وحدة من موديل في آخر.

**Source**: `catalog/units.xlsx` (مستخدم) أو `catalog/units.seed.json` (موديل 2 مؤقتاً).

---

## GlobalIdState

| Field | Type | Rules |
|-------|------|-------|
| `last_used_id` | int | ≥ 0؛ يُحدَّث بعد كل سحب |
| `category_ranges` | map | مفتاح run_key → `CategoryRange` |
| `updated_at` | ISO datetime | |

### CategoryRange

| Field | Type | Rules |
|-------|------|-------|
| `id_start` | int | أول Id لهذا التصنيف |
| `id_end` | int | آخر Id (يُحدَّث عند الإعادة إن زاد العدد) |
| `product_count` | int | |
| `excel_path` | string | مسار نسبي |
| `images_dir` | string | مسار نسبي |

### State transitions

1. **سحب جديد (تصنيف غير موجود في state)**  
   `id_start = last_used_id + 1` → تعيين ids متتالية → `last_used_id = id_end`.

2. **إعادة سحب (تصنيف موجود)**  
   `id_start` من `category_ranges` → ids من `id_start` إلى `id_start + count - 1` → إن `count < old_count` المعرفات الزائدة تُعلَّم `freed` ولا تُعاد استخدامها → إن `count > old_count` يمتد حتى `id_start + count - 1` وقد يرفع `last_used_id`.

3. **تصفية صور**  
   لا يغيّر `GlobalIdState`.

---

## CategoryRun (عملية سحب)

| Field | Type | Rules |
|-------|------|-------|
| `run_id` | uuid | |
| `module_id` | int | من الواجهة |
| `category_id` | int | |
| `sub_category_id` | int | |
| `source_url` | string | URL صالح |
| `max_pages` | int | 0 = كل الصفحات |
| `start_page` | int | افتراضي 1 |
| `output_dir` | string | مجلد الجذر |
| `excel_filename` | string | |
| `images_folder` | string | اسم فرعي |
| `status` | enum | `pending` \| `running` \| `completed` \| `failed` |
| `stats` | ScrapeStats | |

### ScrapeStats

| Field | Type |
|-------|------|
| `products_total` | int |
| `images_ok` | int |
| `images_failed` | int |
| `bytes_saved` | int |

---

## ProductRow (صف Excel — 29 عمود)

| Field | Type | Source |
|-------|------|--------|
| `Id` | int | GlobalIdState allocator |
| `Name` | string | مصدر / عربية |
| `Description` | string | اختياري |
| `Image` | string | `{images_folder}/product_{Id}.webp` |
| `CategoryId` | int | من الكتالوج |
| `SubCategoryId` | int | من الكتالوج |
| `BrandId` | string/int | افتراضي فارغ |
| `UnitId` | int? | من Unit matcher |
| `Stock` | int | افتراضي 100 |
| `Price` | number | من المصدر |
| `Discount` | int | 0 |
| `DiscountType` | string | `percent` |
| `AvailableTimeStarts` | string | |
| `AvailableTimeEnds` | string | |
| `Variations` | string | |
| `ChoiceOptions` | string | |
| `AddOns` | string | |
| `Attributes` | string | |
| `Tags` | string | مولّد عربي |
| `StoreId` | string | |
| `ModuleId` | int | من الواجهة |
| `Status` | int | 1 |
| `Veg` | int | 0 |
| `Recommended` | int | 0 |
| `IsDefaultProduct` | int | 1 |
| `IsPrescriptionReq` | int | 0 (صيدلية: قابل للتجاوز) |
| `CommonConditions` | string | |
| `IsBasic` | int | 1 |
| `QuantityUnit` | number/string | رقم فقط عند الوزن |

**Uniqueness**: داخل التصنيف — `source_url` أو SKU المصدر فريد.

---

## ProductImage

| Field | Type | Rules |
|-------|------|-------|
| `product_id` | int | = ProductRow.Id |
| `filename` | string | `product_{id padded}.webp` |
| `relative_path` | string | تحت `images_folder` |
| `source_url` | string | URL الأصلي |
| `size_bytes` | int | بعد الضغط |

---

## CatalogConfig (ملفات)

| File | Contents |
|------|----------|
| `catalog/modules.json` | Module[] |
| `catalog/categories.json` | Category[] nested |
| `catalog/units.xlsx` | Unit rows (user) |
| `catalog/units.seed.json` | Unit[] fallback module 2 |

---

## Validation Rules Summary

| Rule | Enforcement |
|------|-------------|
| FR-002/003 | `IdAllocator` reads/writes `global_state.json` |
| FR-021 | Re-scrape uses stored `id_start` |
| FR-005/006 | `ImageNaming.format(id)` |
| FR-009/022 | `Catalog.get_units(module_id)` non-empty or abort |
| FR-010 | `UnitMatcher.parse(name, module_id)` |
| SC-003 | Integration test: two runs, ids contiguous |
