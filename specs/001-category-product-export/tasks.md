# Tasks: نظام تصدير المنتجات تصنيفاً بتصنيف

**Input**: Design documents from `/specs/001-category-product-export/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: اختبارات وحدة للمنطق الحرج (ترقيم، صور، كتالوج) حسب plan.md — ليست TDD إلزامية لكل قصة.

**Organization**: مهام مجمّعة حسب قصص المستخدم لتمكين التنفيذ والاختبار المستقل.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: يمكن تنفيذه بالتوازي (ملفات مختلفة، لا يعتمد على مهام غير مكتملة)
- **[Story]**: يربط المهمة بقصة المستخدم (US1–US6)

## Path Conventions

- جذر المشروع: `/Users/mac/Desktop/scripngproducet/`
- حزمة السحب: `pipeline/`
- الواجهة: `app/ui.py`
- الكتالوج: `catalog/`
- الحالة: `data/global_state.json`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: تهيئة الهيكل والاعتماديات

- [ ] T001 Create project directory structure (`app/`, `pipeline/`, `pipeline/scrape/`, `catalog/`, `data/`, `output/`, `tests/unit/`, `tests/integration/`) per plan.md
- [ ] T002 Add `streamlit` and `pytest` to `requirements.txt`
- [ ] T003 [P] Create `pipeline/__init__.py` and `pipeline/errors.py` with `PipelineError` codes (`UNITS_MISSING`, `CATALOG_INVALID`, `SCRAPE_FAILED`, `STATE_CORRUPT`)
- [ ] T004 [P] Create `catalog/modules.json` with modules 1–6 active and 7–8 `active: false`
- [ ] T005 [P] Create `catalog/units.seed.json` with module 2 units (كيلو `UnitId=2`, غرام `UnitId=3`) and aliases
- [ ] T006 [P] Add `output/` and `data/` to `.gitignore` (keep `data/.gitkeep` if needed)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: بنية تحتية تمنع بدء قصص المستخدم حتى اكتمالها

**⚠️ CRITICAL**: لا تبدأ قصص المستخدم قبل إنهاء هذه المرحلة

- [ ] T007 Create `catalog/categories.json` skeleton with module 2 example (e.g. fruits `CategoryId=253`, subcategories with `output_slug`)
- [ ] T008 Implement `pipeline/catalog.py` to load modules, categories, units from `units.xlsx` or `units.seed.json` fallback
- [ ] T009 Implement `pipeline/id_state.py` with `allocate()`, rescrape replace logic, and `data/global_state.json` persistence per `contracts/global-state.schema.json`
- [ ] T010 [P] Create `tests/unit/test_id_state.py` covering contiguous ids and rescrape same `id_start`
- [ ] T011 [P] Create `tests/unit/test_catalog.py` covering active modules 1–6 only and `UNITS_MISSING` for module without units
- [ ] T012 [P] Extract Seoudi GraphQL logic from `scraper.py` into `pipeline/scrape/seoudi_graphql.py`
- [ ] T013 [P] Extract Instashop Playwright logic from `scraper.py` into `pipeline/scrape/instashop.py`
- [ ] T014 [P] Extract HTML BeautifulSoup logic from `scraper.py` into `pipeline/scrape/html_scraper.py`
- [ ] T015 Implement `pipeline/scrape/detector.py` to route URL to seoudi / instashop / html scraper
- [ ] T016 Implement `pipeline/images.py` with WebP conversion (quality 85), `product_{id}.webp` naming, and 3-attempt download retry
- [ ] T017 [P] Create `tests/unit/test_images.py` for filename padding and `Id` ↔ filename match
- [ ] T018 Implement `pipeline/exporter.py` writing 29-column `Products` sheet per `EXCEL_COLUMNS` in `scraper.py`
- [ ] T019 Create `pipeline/runner.py` skeleton with `run_category_job()` signature per `contracts/pipeline-service.md` and progress callback hooks

**Checkpoint**: الكتالوج، الترقيم، محركات السحب، الصور، والتصدير جاهزون للربط

---

## Phase 3: User Story 1 — واجهة اختيار الموديل والتصنيف (Priority: P1) 🎯 MVP

**Goal**: واجهة Streamlit لاختيار موديل 1–6 وتصنيف رئيسي/فرعي مع تعبئة المعرفات تلقائياً

**Independent Test**: فتح `app/ui.py`، اختيار «خضروات وفواكه» → فواكه؛ التحقق أن `ModuleId`/`CategoryId`/`SubCategoryId` تطابق `catalog/categories.json` دون تشغيل سحب

### Implementation for User Story 1

- [ ] T020 [US1] Add `list_modules()`, `list_categories()`, `list_subcategories()`, `get_units()` APIs in `pipeline/catalog.py`
- [ ] T021 [US1] Create `app/ui.py` with Streamlit module dropdown showing only active modules 1–6
- [ ] T022 [US1] Add cascading category and subcategory selectboxes in `app/ui.py`
- [ ] T023 [US1] Display read-only preview of `ModuleId`, `CategoryId`, `SubCategoryId` in `app/ui.py`
- [ ] T024 [US1] Display per-module units table from catalog in `app/ui.py`
- [ ] T025 [US1] Block UI scrape section with clear error when selected module has no units in `catalog/units.xlsx` or seed in `app/ui.py`

**Checkpoint**: الواجهة تعرض الموديلات والتصنيفات والوحدات بشكل صحيح

---

## Phase 4: User Story 2 — سحب تصنيف وإنتاج حزمة جاهزة (Priority: P1)

**Goal**: عملية سحب واحدة تنتج Excel + صور WebP بترقيم عالمي متواصل

**Independent Test**: سحب تصنيف فواكه؛ التحقق من `output/{slug}/fruits.xlsx` و`fruits_images/product_NNN.webp` مع `Id` عالمي يتابع `global_state.json`

### Implementation for User Story 2

- [ ] T026 [US2] Implement pre-scrape `id_state.allocate(run_key, count, rescrape)` in `pipeline/runner.py`
- [ ] T027 [US2] Wire `pipeline/scrape/detector.py` product fetch with pagination/scroll in `pipeline/runner.py`
- [ ] T028 [US2] Build product rows with allocated `Id` and write Excel via `pipeline/exporter.py` in `pipeline/runner.py`
- [ ] T029 [US2] Implement rescrape replace flow (reuse `id_start`, remove orphaned images) per FR-021 in `pipeline/runner.py`
- [ ] T030 [US2] Add source URL, `max_pages`, `start_page`, `output_dir`, `excel_filename`, `images_folder` inputs in `app/ui.py`
- [ ] T031 [US2] Add «بدء السحب» button calling `run_category_job()` with progress display in `app/ui.py`
- [ ] T032 [US2] Refactor `scraper.py` CLI to delegate to `pipeline/runner.py` with `--module-id`, `--category-id`, `--sub-category-id`, `--rescrape` flags

**Checkpoint**: سحب كامل من CLI أو الواجهة ينتج Excel وصور بمعرفات عالمية

---

## Phase 5: User Story 3 — صور WebP ومتطابقة مع المعرف العالمي (Priority: P1)

**Goal**: كل صورة WebP مضغوطة واسمها يطابق `Id` العالمي (بما فيه >999)

**Independent Test**: بعد سحب 100+ منتج عالمياً، التحقق أن `product_100.webp` يطابق `Id=100` وأن 80%+ صور أصغر من الأصل

### Implementation for User Story 3

- [ ] T033 [US3] Add dynamic zero-padding `width=max(3,len(str(id)))` in `pipeline/images.py`
- [ ] T034 [US3] Ensure `Image` column uses `{images_folder}/product_{id_padded}.webp` in `pipeline/exporter.py`
- [ ] T035 [US3] Continue run on single image failure leaving `Image` empty in `pipeline/runner.py`
- [ ] T036 [US3] Show `images_ok`, `images_failed`, and total bytes saved in `app/ui.py` after run

**Checkpoint**: 100% صفوف ذات صور ناجحة تطابق `Id` ↔ اسم الملف

---

## Phase 6: User Story 4 — بيانات استيراد كاملة وقابلة للبحث (Priority: P2)

**Goal**: Tags عربية، وحدات من الكتالوج، وقيم افتراضية صحيحة لكل موديل

**Independent Test**: فتح Excel مُصدَّر؛ التحقق من `ModuleId`, `Tags`, `UnitId`, `QuantityUnit`, `IsDefaultProduct=1` لعينة منتجات

### Implementation for User Story 4

- [ ] T037 [US4] Implement `pipeline/units_matcher.py` parsing weight from name using module units and aliases
- [ ] T038 [US4] Port `build_search_tags()` logic from `update_fruits_excel.py` into `pipeline/tags.py`
- [ ] T039 [US4] Integrate `units_matcher` and `tags` into product row builder in `pipeline/runner.py`
- [ ] T040 [US4] Apply per-module `IMPORT_DEFAULTS` overrides from `catalog/modules.json` in `pipeline/exporter.py`
- [ ] T041 [US4] Support Arabic `Name` from source or optional per-category name map in `catalog/categories.json` via `pipeline/runner.py`

**Checkpoint**: Excel جاهز للاستيراد دون تعديل يدوي لمعظم الصفوف

---

## Phase 7: User Story 5 — تصفية وإدارة الصور (Priority: P2)

**Goal**: تصفية الصور حسب Excel مرجعي مع نقل الزائد لمجلد احتياطي

**Independent Test**: تشغيل التصفية على `fruits.xlsx` + مجلد صور؛ يبقى فقط الصور المذكورة في عمود `Image`

### Implementation for User Story 5

- [ ] T042 [US5] Implement `filter_by_excel()` in `pipeline/images.py` moving extras to `{images_dir}_removed/`
- [ ] T043 [US5] Add «تصفية الصور» section with Excel path input in `app/ui.py`
- [ ] T044 [US5] Display missing images report after filter in `app/ui.py`
- [ ] T045 [US5] Show image folder file count and total size in `app/ui.py` status panel

**Checkpoint**: تصفية تعمل دون كسر الترقيم العالمي في Excel

---

## Phase 8: User Story 6 — دعم مصادر متعددة (Priority: P2)

**Goal**: سعودي GraphQL، إنستاشوب Playwright، وHTML عام بنفس مخرجات Pipeline

**Independent Test**: سحب تجريبي (أو mock) من كل نوع مصدر؛ نفس بنية Excel والصور

### Implementation for User Story 6

- [ ] T046 [US6] Wire Seoudi GraphQL multi-page `url_path` filter in `pipeline/runner.py`
- [ ] T047 [US6] Wire Instashop non-headless scroll with configurable pause in `pipeline/runner.py`
- [ ] T048 [US6] Allow per-run HTML `SELECTORS` override via catalog or UI in `pipeline/scrape/html_scraper.py`
- [ ] T049 [US6] Create `tests/integration/test_pipeline_mock.py` with mocked responses for each scraper type

**Checkpoint**: كشف المصدر التلقائي يعمل لثلاثة أنواع مواقع

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: كتالوج كامل، توثيق، تحقق نهائي

- [ ] T050 [P] Populate `catalog/categories.json` with all user category/subcategory IDs across modules 1–6
- [ ] T051 [P] Import user `catalog/units.xlsx` when provided and validate all active modules have units in `pipeline/catalog.py`
- [ ] T052 Update `README.md` with Streamlit launch, catalog files, and global id behavior
- [ ] T053 Run manual validation per `specs/001-category-product-export/quickstart.md` on Seoudi fruits category
- [ ] T054 Remove or deprecate standalone `update_fruits_excel.py` after logic merged into `pipeline/tags.py` and `pipeline/runner.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: لا تبعيات — ابدأ فوراً
- **Phase 2 (Foundational)**: تعتمد على Phase 1 — **تمنع** كل قصص المستخدم
- **Phase 3 (US1)**: تعتمد على T007–T008 (كتالوج)
- **Phase 4 (US2)**: تعتمد على Phase 2 + US1 catalog APIs
- **Phase 5 (US3)**: تعتمد على T016؛ يمكن موازاة جزء من US2 بعد T028
- **Phase 6 (US4)**: تعتمد على US2 (صفوف منتجات)
- **Phase 7 (US5)**: تعتمد على US2 (مجلد صور + Excel)
- **Phase 8 (US6)**: T012–T015 في Foundational؛ T046–T048 تكامل في runner بعد US2
- **Phase 9 (Polish)**: بعد القصص المطلوبة

### User Story Dependencies

| Story | يعتمد على | يُختبر مستقلاً |
|-------|-----------|----------------|
| US1 | Foundational catalog | ✅ بدون سحب |
| US2 | US1 + Foundational | ✅ سحب كامل |
| US3 | US2 (صور موجودة) | ✅ فحص تسمية/حجم |
| US4 | US2 | ✅ فحص أعمدة Excel |
| US5 | US2 | ✅ تصفية فقط |
| US6 | Foundational scrapers + US2 | ✅ mock لكل مصدر |

### Parallel Opportunities

```bash
# Phase 1 — بالتوازي:
T003, T004, T005, T006

# Phase 2 — استخراج السحب بالتوازي:
T012, T013, T014  # ثم T015 يعتمد عليهم

# Phase 2 — اختبارات بالتوازي:
T010, T011, T017

# Phase 9 — بالتوازي:
T050, T051
```

---

## Parallel Example: User Story 1

```bash
# بعد T020، يمكن موازاة بناء أقسام الواجهة:
T021: module dropdown in app/ui.py
T024: units table in app/ui.py
# ثم T022 → T023 → T025 (تسلسل cascade)
```

---

## Implementation Strategy

### MVP First (US1 + US2 core)

1. Phase 1: Setup
2. Phase 2: Foundational
3. Phase 3: US1 — واجهة اختيار الموديل/التصنيف
4. Phase 4: US2 — سحب فواكه سعودي (موديل 2)
5. **توقف وتحقق**: Excel + WebP + ترقيم عالمي

### Incremental Delivery

1. Setup + Foundational → أساس جاهز
2. US1 → واجهة كتالوج
3. US2 + US3 → سحب وصور (P1 كامل)
4. US4 → Tags ووحدات
5. US5 → تصفية صور
6. US6 → تأكيد المصادر الثلاثة
7. Polish → كتالوج كامل من المستخدم

### Suggested MVP Scope

- **الحد الأدنى**: T001–T032 (Setup + Foundational + US1 + US2)
- **موديل أول للتجربة**: خضروات وفواكه (2) مع `units.seed.json`
- **يتطلب من المستخدم لاحقاً**: `catalog/units.xlsx`, `catalog/categories.json` كامل

---

## Notes

- لا تُخمَّن `UnitId` لموديلات 1، 3–6 — انتظر `catalog/units.xlsx` من المستخدم (T051)
- إعادة السحب: دائماً `--rescrape` / خيار الواجهة لاستبدال النطاق
- `fruits-vegetables/` مجلد قديم — مرجع فقط؛ المخرجات الجديدة تحت `output/`
