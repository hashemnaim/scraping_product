# Implementation Plan: توثيق ودقة ربط حقول التصدير

**Branch**: `002-catalog-field-mapping` | **Date**: 2026-06-15 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/002-catalog-field-mapping/spec.md`

## Summary

تعزيز نظام السحب الحالي بـ **طبقة توثيق ومراجعة** توضّح مصدر كل حقل حرج في Excel (`CategoryId`, `SubCategoryId`, `UnitId`, `QuantityUnit`, `BrandId`)، وتُنتج **تقرير مراجعة** بعد كل عملية سحب، مع **وسوم ثقة** على الاستنتاجات (وحدة افتراضية، علامة فارغة، سعر/صورة ناقصة). يبقى الربط الأساسي كما هو: التصنيف من اختيار الواجهة، الوحدة والعلامة من اسم المنتج عبر `units_matcher` و`brand_matcher`. تُضاف لاحقاً (P3) **قواعد ربط اختيارية** من نص تصنيف المصدر إلى `SubCategoryId` عبر ملف كتالوج.

## Technical Context

**Language/Version**: Python 3.11+ (المشروع `.venv` على 3.14)  
**Primary Dependencies**: streamlit, openpyxl, pandas (كتالوج), requests, playwright — بدون تبعيات جديدة للمرحلة P1/P2  
**Storage**: `catalog/` (xlsx/csv)، `data/global_state.json`، `data/run_history.jsonl` (جديد)، `output/`  
**Testing**: pytest — وحدة لـ `field_mapping`, `review_report`, `units_matcher`, `brand_matcher`, `category_rules`  
**Target Platform**: تطبيق سطح مكتب macOS (Streamlit + PyInstaller) وتطوير محلي  
**Project Type**: أداة سطح مكتب — pipeline + واجهة Streamlit  
**Performance Goals**: تقرير المراجعة يُبنى في <2 ثانية لـ 500 منتج؛ لا تأخير ملحوظ على مسار السحب  
**Constraints**: لا تغيير في صيغة Excel الـ 29 عموداً؛ الكتالوج يبقى المصدر الوحيد للمعرفات  
**Scale/Scope**: 6 موديلات، مئات المنتجات لكل تشغيل، 3 طبقات أولوية (P1 توثيق+وحدات، P2 مراجعة+علامات، P3 قواعد تصنيف)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| الدستور مُفعَّل | ⚠️ N/A | `constitution.md` قالب فارغ |
| البساطة | ✅ Pass | توسيع `pipeline/` و`app/ui.py` دون خدمات جديدة |
| عدم كسر 001 | ✅ Pass | يبني على `runner.py` و`exporter.py` الحاليين |
| اختبارات المنطق الحرج | ✅ Pass | وحدات، علامات، تقرير مراجعة |
| الكتالوج مصدر المعرفات | ✅ Pass | FR-020 محفوظ |

**Post-design re-check**: ✅ لا انتهاكات — التصميم يضيف metadata وUI فقط دون تغيير عقد Excel.

## Project Structure

### Documentation (this feature)

```text
specs/002-catalog-field-mapping/
├── plan.md                 # هذا الملف
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── field-enrichment.schema.json
│   ├── review-report.schema.json
│   └── category-mapping-rules.schema.json
└── tasks.md                # /speckit.tasks
```

### Source Code (repository root)

```text
scripngproducet/
├── app/
│   └── ui.py                          # ملخص قبل السحب + تقرير بعد السحب
├── pipeline/
│   ├── runner.py                      # يُرجع enrichment + review_report
│   ├── field_mapping.py               # NEW: مصادر الحقول، ثوابت العرض
│   ├── review_report.py               # NEW: بناء تقرير المراجعة
│   ├── category_rules.py              # NEW (P3): قواعد تصنيف المصدر → SubCategoryId
│   ├── run_history.py                 # NEW: سجل تشغيل JSONL
│   ├── units_matcher.py               # يُرجع reason/confidence
│   ├── brand_matcher.py               # يُرجع match_tier + reason
│   ├── exporter.py                    # بدون تغيير أعمدة
│   └── catalog.py                     # تحميل category_mapping_rules.xlsx
├── catalog/
│   ├── units.xlsx
│   ├── brands.csv
│   ├── brand_aliases.csv
│   └── category_mapping_rules.xlsx    # NEW (P3): pattern → sub_category_id
├── data/
│   ├── global_state.json
│   └── run_history.jsonl              # NEW
└── tests/unit/
    ├── test_field_mapping.py
    ├── test_review_report.py
    ├── test_units_matcher.py            # توسيع
    ├── test_brand_matcher.py            # توسيع
    └── test_category_rules.py           # P3
```

**Structure Decision**: توسيع الحزمة الحالية `pipeline/` بملفات صغيرة متخصصة؛ الواجهة في `app/ui.py`؛ قواعد الربط في `catalog/` كملف Excel اختياري.

## Phase 0: Research

**Status**: ✅ Complete — see [research.md](./research.md)

| Topic | Decision |
|-------|----------|
| مصدر CategoryId/SubCategoryId | اختيار الواجهة لكل عملية سحب (موجود) |
| مصدر UnitId/QuantityUnit | استنتاج من الاسم + `units_matcher` + قواعد التصنيف (موجود، يُوسَّع بالوسوم) |
| مصدر BrandId | `brand_matcher` + brands.csv (موجود) |
| توثيق للمستخدم | لوحة ملخص ثابتة + قيم معاينة حية قبل السحب |
| تقرير المراجعة | كائن JSON في `CategoryRunResult` + عرض Streamlit |
| قواعد تصنيف المصدر | ملف `category_mapping_rules.xlsx` — P3 |
| سجل التشغيل | `data/run_history.jsonl` سطر لكل عملية |

## Phase 1: Design

**Status**: ✅ Complete

| Artifact | Path |
|----------|------|
| Data model | [data-model.md](./data-model.md) |
| Contracts | [contracts/](./contracts/) |
| Quickstart | [quickstart.md](./quickstart.md) |

## Phase 2: Implementation Outline (for `/speckit.tasks`)

### Milestone A — توثيق مصدر الحقول (P1, US1)

1. **`pipeline/field_mapping.py`**
   - `FIELD_SOURCES`: تعريف كل حقل حرج → `source` ∈ {`user_selection`, `scraped`, `inferred_name`, `catalog_default`, `inferred_rule`}
   - `build_pre_scrape_summary(module_id, category_id, sub_category_id, units)` → نص/بنية للواجهة
2. **`app/ui.py`**
   - Expander «كيف تُملأ حقول Excel؟» فوق زر السحب
   - جدول مصدر الحقول مع أيقونات (اختيارك / من الموقع / من الاسم)
   - تذكير: «رابط واحد = تصنيف فرعي واحد»

### Milestone B — وسوم ثقة على الاستنتاج (P1, US3)

3. **`units_matcher.py`**
   - `MatchResult(unit_id, quantity_unit, confidence, reason)` بدل tuple خام
   - `confidence=low` عند: افتراضي قطعة، اسم غامض، وحدات متعددة في الاسم
4. **`brand_matcher.py`**
   - `BrandMatchResult(brand_id, confidence, reason)` — `none` عند عدم مطابقة
5. **`runner.py`**
   - يجمع `FieldEnrichment` لكل منتج ويمرّره لتقرير المراجعة

### Milestone C — تقرير المراجعة (P2, US5)

6. **`pipeline/review_report.py`**
   - `build_review_report(rows, enrichments) → ReviewReport`
   - تجميع: `default_unit`, `missing_brand`, `missing_price`, `failed_image`, `ambiguous_unit`
7. **`CategoryRunResult`**
   - حقول جديدة: `review_report`, `mapping_stats`
8. **`app/ui.py`**
   - قسم بعد السحب: metrics + expander قائمة المنتجات المُوسومة + dataframe قابل للتصفية

### Milestone D — سجل التشغيل (P2, FR-018)

9. **`pipeline/run_history.py`**
   - `append_run_log(entry)` إلى `data/run_history.jsonl`
   - يتضمن: timestamp, source_url, run_key, counts, warning_rates

### Milestone E — قواعد ربط التصنيف (P3, US6)

10. **`catalog/category_mapping_rules.xlsx`**
    - أعمدة: `module_id`, `pattern`, `sub_category_id`, `priority`
11. **`pipeline/category_rules.py`**
    - `resolve_subcategory(source_category_text, default_sub_id, rules)` → id + rule_applied
12. **`runner.py`**
    - عند تفعيل القواعد: override `SubCategoryId` per-product مع توسيم `category_override` في المراجعة

### Milestone F — اختبارات وتوثيق

**Status**: ✅ Complete

13. عينات اختبار SC-002/SC-003 في `tests/unit/`
14. `quickstart.md` + بناء M1

## Risk & Mitigation

| Risk | Mitigation |
|------|------------|
| المستخدم يختار تصنيفاً خاطئاً | ملخص قبل السحب + توصية «رابط = تصنيف» |
| مطابقة علامة خاطئة | الإبقاء على فارغ عند ثقة منخفضة؛ عرض في التقرير |
| تعقيد قواعد P3 | ملف اختياري؛ الافتراضي = سلوك 001 |
| تضخم `runner.py` | فصل `review_report` و`field_mapping` |

## Complexity Tracking

> لا انتهاكات تبرر تعقيداً إضافياً.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
