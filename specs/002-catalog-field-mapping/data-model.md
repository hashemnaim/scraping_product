# Data Model: توثيق ودقة ربط حقول التصدير

**Branch**: `002-catalog-field-mapping` | **Date**: 2026-06-15

## Entity Relationship Overview

```text
CategoryRun (موجود — 001)
  ├── user selection → ModuleId, CategoryId, SubCategoryId  [ثابت لكل الصفوف ما لم تُفعَّل القواعد]
  ├── scrape → raw product { name, price, image_url, category? }
  └── enrich → FieldEnrichment[] per product
        ├── unit_match: UnitMatchResult
        ├── brand_match: BrandMatchResult
        └── warnings: WarningFlag[]

ReviewReport (جديد)
  ├── summary counts by warning type
  └── items: ReviewItem[] (product_id, name, warnings, inferred fields)

CategoryMappingRule (جديد — P3)
  ├── module_id, pattern, sub_category_id, priority
  └── applied per product when source category text matches

RunHistoryEntry (جديد)
  └── appended to data/run_history.jsonl
```

---

## FieldSource (ثابت — metadata)

| Field | `source` | ملاحظة |
|-------|----------|--------|
| `CategoryId` | `user_selection` | من الواجهة |
| `SubCategoryId` | `user_selection` أو `inferred_rule` | قاعدة P3 فقط |
| `UnitId` | `inferred_name` أو `catalog_default` | قطعة افتراضية = default |
| `QuantityUnit` | `inferred_name` أو `catalog_default` | |
| `BrandId` | `inferred_name` أو فارغ | لا default خاطئ |
| `Name`, `Price`, `Image` | `scraped` | من المصدر |

---

## UnitMatchResult

| Field | Type | Rules |
|-------|------|-------|
| `unit_id` | int? | من وحدات الموديل |
| `quantity_unit` | str? | رقم فقط عادةً |
| `confidence` | enum | `high`, `medium`, `low` |
| `reason` | string | مثل `pattern_kg`, `default_piece`, `category_forced_piece` |

**Rules**:
- `high`: نمط واضح في الاسم (250 غرام، 1 كيلو)
- `medium`: قطعة صريحة في الاسم
- `low`: افتراضي قطعة/1 أو تعارض أنماط

---

## BrandMatchResult

| Field | Type | Rules |
|-------|------|-------|
| `brand_id` | int? | null = لا مطابقة |
| `confidence` | enum | `high`, `medium`, `low`, `none` |
| `reason` | string | `alias`, `substring`, `fuzzy`, `none` |

**Rules**:
- لا يُكتب `brand_id` عند `confidence=low` إلا إذا تجاوزت العتبة — سياسة: **none أفضل من خطأ**

---

## FieldEnrichment (per product)

| Field | Type |
|-------|------|
| `product_id` | int |
| `product_name` | string |
| `unit` | UnitMatchResult |
| `brand` | BrandMatchResult |
| `warnings` | WarningFlag[] |
| `source_category` | str? |
| `resolved_sub_category_id` | int? |

---

## WarningFlag

| Value | Meaning |
|-------|---------|
| `default_unit` | UnitId من افتراضي قطعة |
| `ambiguous_unit` | أكثر من وحدة في الاسم |
| `missing_brand` | BrandId فارغ |
| `missing_price` | Price فارغ |
| `failed_image` | فشل تحميل الصورة |
| `category_rule_applied` | SubCategoryId من قاعدة وليس الواجهة |
| `category_rule_conflict` | تعارض قاعدتين — يُستخدم الاحتياطي |

---

## ReviewReport

| Field | Type |
|-------|------|
| `products_total` | int |
| `ready_for_import` | bool |
| `counts` | dict[WarningFlag → int] |
| `items` | ReviewItem[] |
| `mapping_stats` | `{ inferred_pct, default_pct, missing_brand_pct }` |

---

## ReviewItem

| Field | Type |
|-------|------|
| `product_id` | int |
| `name` | string |
| `warnings` | WarningFlag[] |
| `unit_id` | int? |
| `quantity_unit` | str? |
| `brand_id` | int? |
| `details` | string |

---

## CategoryMappingRule (P3)

| Field | Type | Rules |
|-------|------|-------|
| `module_id` | int | FK → Module |
| `pattern` | string | نص عربي/إنجليزي للمطابقة (contains) |
| `sub_category_id` | int | FK → SubCategory |
| `priority` | int | أعلى = أولوية عند التعارض |
| `active` | bool | default true |

**Source**: `catalog/category_mapping_rules.xlsx`

---

## RunHistoryEntry

| Field | Type |
|-------|------|
| `timestamp` | ISO8601 |
| `run_key` | string |
| `source_url` | string |
| `module_id` | int |
| `category_id` | int |
| `sub_category_id` | int |
| `products_total` | int |
| `warning_counts` | object |
| `excel_path` | string |

**Storage**: append-only `data/run_history.jsonl`

---

## State Transitions

```text
[User selects catalog] → [Pre-scrape summary shown]
       ↓
[Scrape raw products]
       ↓
[For each product: enrich unit/brand + collect warnings]
       ↓ (P3 optional)
[Apply category rules → may override SubCategoryId]
       ↓
[Build Excel rows + ReviewReport + append run_history]
       ↓
[UI shows results + review expander]
```

---

## Validation Rules

- `SubCategoryId` من الواجهة مطلوب قبل السحب (موجود ضمنياً عبر selectbox + st.stop)
- `UnitId` لا يُترك فارغاً في Excel — `finalize_unit_for_export` يضمن قطعة
- `BrandId` فارغ مسموح
- قواعد P3: إن لم يطابق أي pattern → `sub_category_id` من الواجهة
