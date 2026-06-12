# Implementation Plan: نظام تصدير المنتجات تصنيفاً بتصنيف

**Branch**: `001-category-product-export` | **Date**: 2026-06-09 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-category-product-export/spec.md`

## Summary

بناء نظام موحّد لسحب المنتجات **تصنيفاً بتصنيف** من مصادر متعددة (سعودي GraphQL، إنستاشوب Playwright، HTML)، مع **واجهة Streamlit** لاختيار الموديل (1–6) والتصنيف، **ترقيم عالمي** للمعرفات والصور WebP، وملفات Excel جاهزة للاستيراد (29 عمود). يُعاد هيكلة `scraper.py` إلى حزمة `pipeline/` مع كتالوج مركزي وملف حالة `global_state.json`. إعادة السحب **تستبدل** نطاق معرفات التصنيف نفسه.

## Technical Context

**Language/Version**: Python 3.11+ (المشروع يستخدم 3.14 في `.venv`)  
**Primary Dependencies**: requests, beautifulsoup4, openpyxl, lxml, Pillow, playwright, **streamlit** (جديد), **pytest** (اختبارات)  
**Storage**: ملفات JSON/YAML/XLSX محلية (`catalog/`, `data/global_state.json`, `output/`)  
**Testing**: pytest — وحدة لـ `id_state`, `catalog`, `images`, `exporter`  
**Target Platform**: macOS محلي (مستخدم واحد)  
**Project Type**: أداة سطح مكتب/محلية — CLI + واجهة Streamlit  
**Performance Goals**: سحب 400 منتج مع صور في <30 دقيقة؛ ضغط WebP يقلل الحجم ≥80% من الأصل  
**Constraints**: Instashop يتطلب Playwright غير headless؛ ترقيم عالمي دون تعارض؛ `units.xlsx` مطلوب لكل موديل نشط  
**Scale/Scope**: 6 موديلات، مئات المنتجات لكل تصنيف، آلاف صور WebP إجمالاً

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| الدستور مُفعَّل | ⚠️ N/A | `constitution.md` قالب فارغ — لا قيود إلزامية |
| البساطة | ✅ Pass | حزمة Python واحدة + Streamlit؛ لا microservices |
| CLI محفوظ | ✅ Pass | `scraper.py` يبقى غلافاً |
| اختبارات المنطق الحرج | ✅ Pass | ترقيم، تسمية صور، كتالوج |
| تبعية المستخدم (units.xlsx) | ✅ Documented | seed لموديل 2 فقط حتى الرفع |

**Post-design re-check**: ✅ لا انتهاكات — التصميم يوسّع المشروع الحالي دون تعقيد زائد.

## Project Structure

### Documentation (this feature)

```text
specs/001-category-product-export/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── category-run.schema.json
│   ├── global-state.schema.json
│   └── pipeline-service.md
└── tasks.md              # /speckit.tasks
```

### Source Code (repository root)

```text
scripngproducet/
├── app/
│   └── ui.py                 # Streamlit: موديل → تصنيف → سحب → تصفية
├── pipeline/
│   ├── __init__.py
│   ├── runner.py             # run_category_job()
│   ├── catalog.py            # تحميل modules/categories/units
│   ├── id_state.py           # ترقيم عالمي + إعادة سحب
│   ├── exporter.py           # Excel 29 عمود
│   ├── images.py             # WebP + filter
│   ├── tags.py               # Tags عربية
│   ├── units_matcher.py      # استخراج وزن/وحدة
│   └── scrape/
│       ├── __init__.py
│       ├── detector.py       # كشف المصدر
│       ├── seoudi_graphql.py
│       ├── instashop.py
│       └── html_scraper.py
├── catalog/
│   ├── modules.json
│   ├── categories.json
│   ├── units.seed.json       # موديل 2 مؤقتاً
│   └── units.xlsx            # من المستخدم (غير موجود بعد)
├── data/
│   └── global_state.json     # يُنشأ عند أول تشغيل
├── output/                   # مخرجات التصنيفات
├── tests/
│   ├── unit/
│   │   ├── test_id_state.py
│   │   ├── test_images.py
│   │   └── test_catalog.py
│   └── integration/
│       └── test_pipeline_mock.py
├── scraper.py                # CLI → pipeline.runner
├── requirements.txt
└── README.md
```

**Structure Decision**: إعادة هيكلة تدريجية من ملف `scraper.py` أحادي إلى `pipeline/` مع الإبقاء على CLI. الواجهة في `app/ui.py`. الكتالوج والحالة في `catalog/` و`data/`.

## Phase 0: Research

**Status**: ✅ Complete — see [research.md](./research.md)

| Topic | Decision |
|-------|----------|
| UI | Streamlit |
| State | `data/global_state.json` |
| Catalog | JSON + `units.xlsx` |
| Images | Pillow WebP q=85 |
| Re-scrape | Replace id range |
| Modules 7–8 | Reserved, hidden |

## Phase 1: Design

**Status**: ✅ Complete

| Artifact | Path |
|----------|------|
| Data model | [data-model.md](./data-model.md) |
| Contracts | [contracts/](./contracts/) |
| Quickstart | [quickstart.md](./quickstart.md) |

## Phase 2: Implementation Outline (for `/speckit.tasks`)

### Milestone 1 — الأساس (P1)

1. إنشاء `pipeline/id_state.py` + اختبارات الترقيم العالمي وإعادة السحب.
2. إنشاء `pipeline/catalog.py` + `catalog/modules.json`, `categories.json`, `units.seed.json`.
3. استخراج منطق السحب من `scraper.py` إلى `pipeline/scrape/*`.
4. `pipeline/exporter.py` + `pipeline/images.py` (نقل من scraper مع تسمية ديناميكية للخانات).
5. `pipeline/runner.py` — تجميع المسار الكامل.

### Milestone 2 — الواجهة (P1)

6. `app/ui.py` — اختيار موديل/تصنيف، رابط، تشغيل، تقدم.
7. ربط `IMPORT_DEFAULTS` بإعدادات الموديل من الكتالوج.

### Milestone 3 — البيانات والوسوم (P2)

8. `pipeline/units_matcher.py` — قراءة وحدات الموديل من xlsx.
9. `pipeline/tags.py` — دمج منطق `update_fruits_excel.py`.
10. زر تصفية الصور في الواجهة.

### Milestone 4 — الكتالوج الكامل (P2)

11. تعبئة `catalog/categories.json` بتصنيفات المستخدم (معرفات حقيقية).
12. استيراد `catalog/units.xlsx` عند توفيره من المستخدم.
13. تحديث README وquickstart.

### Milestone 5 — اختبار وتحقق (P2)

14. اختبار تكامل: سحبان متتاليان → ids متصلة.
15. اختبار إعادة سحب → نفس `id_start`.
16. تشغيل يدوي على فواكه سعودي كتحقق قبول.

## Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| `units.xlsx` غير مرفوع | seed لموديل 2؛ رفض واضح للباقي |
| `categories.json` فارغ | يحتاج إدخال معرفات من المستخدم قبل كل موديل |
| Playwright / Cloudflare | non-headless؛ رسالة خطأ واضحة |
| ملفات قديمة `fruits-vegetables/` | مرجع فقط؛ المخرجات الجديدة تحت `output/` |

## Complexity Tracking

> لا انتهاكات للدستور تتطلب تبريراً.

| Item | Why | Alternative rejected |
|------|-----|----------------------|
| حزمة `pipeline/` | فصل مسؤوليات | ملف واحد 1500+ سطر |
| Streamlit | واجهة سريعة | Flask+React أثقل |
