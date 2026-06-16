# Tasks: توثيق ودقة ربط حقول التصدير

**Input**: Design documents from `/specs/002-catalog-field-mapping/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: اختبارات وحدة للمنطق الحرج (وحدات، علامات، تقرير مراجعة، قواعد تصنيف) حسب plan.md.

**Organization**: مهام مجمّعة حسب قصص المستخدم — كل قصة قابلة للتنفيذ والاختبار بشكل مستقل قدر الإمكان.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: يمكن تنفيذه بالتوازي (ملفات مختلفة، لا يعتمد على مهام غير مكتملة في نفس الملف)
- **[Story]**: يربط المهمة بقصة المستخدم (US1–US6)

## Path Conventions

- جذر المشروع: `scripngproducet/`
- حزمة السحب: `pipeline/`
- الواجهة: `app/ui.py`
- الكتالوج: `catalog/`
- الحالة: `data/`
- الاختبارات: `tests/unit/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: تهيئة الملفات والثوابت المشتركة للميزة 002

- [x] T001 [P] Add `WarningFlag` and `FieldSource` enums/constants in `pipeline/field_mapping.py` per `data-model.md`
- [x] T002 [P] Add `FIELD_SOURCES` map for critical Excel columns (`CategoryId`, `SubCategoryId`, `UnitId`, `QuantityUnit`, `BrandId`, `Name`, `Price`, `Image`) in `pipeline/field_mapping.py`
- [x] T003 [P] Register `category_mapping_rules.xlsx` in `pipeline/constants.py` `CATALOG_FILES` (label: قواعد ربط التصنيف) for P3 upload in sidebar
- [x] T004 Ensure `data/` directory exists on first run via `pipeline/paths.py` `ensure_user_layout()` (already creates `data/` — verify no change needed or add `run_history.jsonl` touch)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: أنواع البيانات والنتائج الموسّعة التي تعتمد عليها كل قصص المستخدم

**⚠️ CRITICAL**: لا تبدأ قصص المستخدم قبل إنهاء T005–T008

- [x] T005 Define `UnitMatchResult` and `BrandMatchResult` dataclasses in `pipeline/units_matcher.py` and `pipeline/brand_matcher.py` (or shared `pipeline/match_types.py` if preferred to avoid circular imports)
- [x] T006 Define `FieldEnrichment` dataclass in `pipeline/review_report.py` per `contracts/field-enrichment.schema.json`
- [x] T007 Extend `CategoryRunResult` in `pipeline/runner.py` with optional `review_report: dict` and `mapping_stats: dict` fields (backward compatible defaults)
- [x] T008 [P] Add thin wrapper functions keeping backward compatibility: `match_unit_for_category()` continues to work — delegate to new `match_unit_with_meta()` returning `UnitMatchResult`

**Checkpoint**: أنواع النتائج والعقد جاهزة — يمكن البدء بقصص المستخدم

---

## Phase 3: User Story 1 — فهم مصدر كل حقل في Excel (Priority: P1) 🎯 MVP

**Goal**: عرض ملخص واضح قبل السحب يوضّح مصدر كل حقل حرج في Excel

**Independent Test**: فتح `app/ui.py` → تبويب «من موقع» → expander «كيف تُملأ حقول Excel؟» يعرض جدول المصادر والقيم المختارة حالياً دون تشغيل سحب

### Tests for User Story 1

- [x] T009 [P] [US1] Create `tests/unit/test_field_mapping.py` — `FIELD_SOURCES` covers all 5 critical fields; `build_pre_scrape_summary()` returns Arabic labels for each source type

### Implementation for User Story 1

- [x] T010 [US1] Implement `build_pre_scrape_summary(module_id, category_id, sub_category_id, category_name, sub_name, units)` in `pipeline/field_mapping.py`
- [x] T011 [US1] Implement `field_source_rows()` helper returning list of `{field, label_ar, source_ar, icon}` for UI table in `pipeline/field_mapping.py`
- [x] T012 [US1] Add expander «كيف تُملأ حقول Excel؟» in `app/ui.py` (tab website) showing field source table with RTL styling
- [x] T013 [US1] Show live selected `ModuleId`, `CategoryId`, `SubCategoryId` in pre-scrape summary panel in `app/ui.py`
- [x] T014 [US1] Add workflow tip banner «رابط واحد = تصنيف فرعي واحد» above scrape button in `app/ui.py`

**Checkpoint**: المستخدم يرى مصدر كل حقل قبل الضغط على «بدء السحب»

---

## Phase 4: User Story 2 — تشغيل سحب منظم حسب التصنيف الصحيح (Priority: P1)

**Goal**: تأكيد أن التصنيف من اختيار المستخدم فقط، مع تحذيرات واضحة

**Independent Test**: سحب رابط واحد باختيارين فرعيين مختلفين → ملفان Excel يختلفان في `CategoryId`/`SubCategoryId` فقط

### Tests for User Story 2

- [x] T015 [P] [US2] Add test in `tests/unit/test_exporter.py` or new `tests/unit/test_runner_category.py` — all rows in one run share same `CategoryId` and `SubCategoryId` from request

### Implementation for User Story 2

- [x] T016 [US2] Document in pre-scrape summary that source site category text is **not** used for `CategoryId`/`SubCategoryId` (unless P3 rules enabled) in `pipeline/field_mapping.py` + `app/ui.py`
- [x] T017 [US2] Add caption in `app/ui.py` when `source_url` domain changes reminding user to verify subcategory selection matches the URL page
- [x] T018 [US2] Verify `runner.py` always passes `request.category_id` and `request.sub_category_id` to `exporter.build_row()` — add assertion comment or unit test guard

**Checkpoint**: مسار «رابط = تصنيف» موثّق ومُتحقق منه في الكود

---

## Phase 5: User Story 3 — دقة الوحدة وكمية الوحدة (Priority: P1)

**Goal**: استنتاج `UnitId`/`QuantityUnit` مع ثقة وسبب؛ توسيم المنتجات الغامضة

**Independent Test**: تشغيل `pytest tests/unit/test_units_matcher.py` — عينات SC-002 (كيلو خضروات، مل→قطعة سوبرماركت، غرام أجبان، افتراضي قطعة)

### Tests for User Story 3

- [x] T019 [P] [US3] Extend `tests/unit/test_units_matcher.py` — `match_unit_with_meta()` returns `confidence=high` for «طماطم 1 كيلو» in خضروات
- [x] T020 [P] [US3] Extend `tests/unit/test_units_matcher.py` — «حليب 500 مل» in سوبرماركت → piece + `confidence=low` + reason `category_forced_piece`
- [x] T021 [P] [US3] Extend `tests/unit/test_units_matcher.py` — «عرض خاص» → default piece + `warning=default_unit`
- [x] T022 [P] [US3] Extend `tests/unit/test_units_matcher.py` — «6 × 500 مل» → `ambiguous_unit` or lowest-unit policy per spec edge case

### Implementation for User Story 3

- [x] T023 [US3] Implement `match_unit_with_meta(name, units, category_name, subcategory_name) -> UnitMatchResult` in `pipeline/units_matcher.py`
- [x] T024 [US3] Map confidence levels: `high` (clear pattern), `medium` (explicit piece), `low` (default/fallback) in `pipeline/units_matcher.py`
- [x] T025 [US3] Detect ambiguous multi-unit names and set `reason=ambiguous_unit` in `pipeline/units_matcher.py`
- [x] T026 [US3] Update `finalize_unit_for_export()` to accept/return `UnitMatchResult` metadata without breaking existing tuple callers
- [x] T027 [US3] In `pipeline/runner.py` loop: call `match_unit_with_meta`, attach unit metadata to `FieldEnrichment`, set `default_unit` warning when `confidence=low`

**Checkpoint**: كل منتج مسحوب يحمل metadata وحدة قابلة للمراجعة

---

## Phase 6: User Story 4 — دقة العلامة التجارية (Priority: P2)

**Goal**: `BrandId` مع ثقة وسبب؛ لا مطابقة خاطئة عند ثقة منخفضة

**Independent Test**: `pytest tests/unit/test_brand_matcher.py` — «بيبسي 330 مل» → brand_id؛ «عرض خاص» → none

### Tests for User Story 4

- [x] T028 [P] [US4] Extend `tests/unit/test_brand_matcher.py` — `match_brand_with_meta()` returns `confidence=high` for known brand substring
- [x] T029 [P] [US4] Extend `tests/unit/test_brand_matcher.py` — unknown name → `brand_id=None`, `confidence=none`
- [x] T030 [P] [US4] Extend `tests/unit/test_brand_matcher.py` — fuzzy match below threshold → none (no false positive)

### Implementation for User Story 4

- [x] T031 [US4] Implement `match_brand_with_meta(product_name, module_id) -> BrandMatchResult` in `pipeline/brand_matcher.py`
- [x] T032 [US4] Keep `match_brand()` as wrapper returning `brand_id` only for backward compatibility
- [x] T033 [US4] In `pipeline/runner.py`: use `match_brand_with_meta`, add `missing_brand` warning when `confidence=none`
- [x] T034 [US4] Show brand match tier in pre-scrape summary example text in `app/ui.py` (static explanation)

**Checkpoint**: العلامات تُستنتج مع شفافية؛ الفارغ أفضل من الخطأ

---

## Phase 7: User Story 5 — تقرير مراجعة قبل الاعتماد على Excel (Priority: P2)

**Goal**: تقرير بعد السحب يلخّص التحذيرات وقائمة المنتجات للمراجعة

**Independent Test**: إكمال سحب → قسم «تقرير المراجعة» يظهر أعداد التحذيرات وقائمة المنتجات المُوسومة

### Tests for User Story 5

- [x] T035 [P] [US5] Create `tests/unit/test_review_report.py` — `build_review_report()` counts `default_unit`, `missing_brand`, `failed_image` correctly
- [x] T036 [P] [US5] Create `tests/unit/test_review_report.py` — `ready_for_import=true` when zero warnings
- [x] T037 [P] [US5] Create `tests/unit/test_review_report.py` — `mapping_stats` percentages match product count

### Implementation for User Story 5

- [x] T038 [US5] Implement `build_review_report(enrichments, rows) -> dict` in `pipeline/review_report.py` per `contracts/review-report.schema.json`
- [x] T039 [US5] Implement `collect_warnings(product, enrichment) -> list[WarningFlag]` in `pipeline/review_report.py` (price empty, image failed, unit, brand)
- [x] T040 [US5] Wire `runner.py` to build `review_report` after row loop and attach to `CategoryRunResult`
- [x] T041 [US5] Add post-scrape «تقرير المراجعة» section in `app/ui.py` — metrics row for each warning type
- [x] T042 [US5] Add expander with filterable dataframe of flagged products (`name`, warnings, `unit_id`, `brand_id`, `details`) in `app/ui.py`
- [x] T043 [US5] Show «جاهز للاستيراد» success banner when `ready_for_import=true` in `app/ui.py`

**Checkpoint**: المستخدم يراجع الاستثناءات دون فتح Excel

---

## Phase 8: User Story 5 (continued) — سجل التشغيل (FR-018)

**Goal**: حفظ سجل JSONL لكل عملية سحب

**Independent Test**: بعد سحب → سطر جديد في `data/run_history.jsonl` يحتوي `run_key`, `warning_counts`

### Tests

- [x] T044 [P] [US5] Create `tests/unit/test_run_history.py` — `append_run_log()` appends valid JSON line to temp file

### Implementation

- [x] T045 [US5] Implement `append_run_log(entry: dict)` in `pipeline/run_history.py` writing to `project_root()/data/run_history.jsonl`
- [x] T046 [US5] Call `append_run_log()` at end of successful `run_category_job()` in `pipeline/runner.py`

**Checkpoint**: سجل تشغيل قابل للتتبع لقياس التحسن (SC-006)

---

## Phase 9: User Story 6 — قواعد ربط تصنيف المصدر (Priority: P3)

**Goal**: ملف قواعد اختياري يربط نص تصنيف الموقع بـ `SubCategoryId`

**Independent Test**: قاعدة «مياه» → sub_category_id 12؛ منتج بتصنيف مصدر «مياه معدنية» يحصل على 12 في Excel

### Tests for User Story 6

- [x] T047 [P] [US6] Create `tests/unit/test_category_rules.py` — `resolve_subcategory()` matches contains pattern
- [x] T048 [P] [US6] Create `tests/unit/test_category_rules.py` — no match → default sub_category_id from UI
- [x] T049 [P] [US6] Create `tests/unit/test_category_rules.py` — conflicting rules → higher priority wins; tie → `category_rule_conflict` warning

### Implementation for User Story 6

- [x] T050 [P] [US6] Add seed `catalog/category_mapping_rules.xlsx` with example rows (`module_id`, `pattern`, `sub_category_id`, `priority`, `active`)
- [x] T051 [US6] Implement `load_category_mapping_rules(module_id)` in `pipeline/catalog.py`
- [x] T052 [US6] Implement `resolve_subcategory(source_text, default_id, rules) -> (sub_id, rule_applied, conflict)` in `pipeline/category_rules.py`
- [x] T053 [US6] Add checkbox «تفعيل قواعد ربط تصنيف الموقع» in `app/ui.py` (default off)
- [x] T054 [US6] In `runner.py`: when rules enabled, per-product override `sub_category_id` in `build_row()`; tag `category_rule_applied` in enrichment
- [x] T055 [US6] Add sidebar upload for `category_mapping_rules.xlsx` via existing catalog upload flow in `app/ui.py`

**Checkpoint**: صفحات مختلطة التصنيف مدعومة اختيارياً

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: تكامل، تطبيق سطح المكتب، والتحقق النهائي

- [x] T056 [P] Add `pipeline.field_mapping`, `pipeline.review_report`, `pipeline.run_history`, `pipeline.category_rules` to `hiddenimports` in `scraping_product.spec` and `scraping_product_m1.spec`
- [x] T057 Run full unit suite: `.venv/bin/python -m pytest tests/unit/ -q`
- [x] T058 [P] Validate `specs/002-catalog-field-mapping/quickstart.md` workflow manually (pre-summary → scrape → review report)
- [x] T059 [P] Rebuild Mac M1 app: `./scripts/build_mac_m1.sh` after UI changes
- [x] T060 Update `specs/002-catalog-field-mapping/checklists/requirements.md` implementation status notes if needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **BLOCKS** all user stories
- **Phase 3–9 (User Stories)**: Depend on Phase 2
  - US1 (Phase 3) → MVP، يمكن إيقاف التنفيذ هنا للعرض
  - US2 (Phase 4) → يعتمد على US1 للنصوص في UI؛ منطق runner موجود
  - US3 (Phase 5) → يعتمد على T005/T008؛ يغذي US5
  - US4 (Phase 6) → يعتمد على T005؛ يغذي US5
  - US5 (Phase 7–8) → يعتمد على US3 + US4 enrichments
  - US6 (Phase 9) → مستقل نسبياً؛ يعتمد على Phase 2 فقط للـ enrichment shape
- **Phase 10 (Polish)**: بعد US1–US5 كحد أدنى؛ US6 اختياري

### User Story Dependencies

| Story | Depends on | Can start after |
|-------|------------|-----------------|
| US1 | Phase 2 | T008 |
| US2 | US1 (UI copy) | T014 |
| US3 | Phase 2 | T008 |
| US4 | Phase 2 | T008 |
| US5 | US3 + US4 | T027, T033 |
| US6 | Phase 2 | T008 (parallel with US3–US5) |

### Parallel Opportunities

```bash
# Phase 1 — بالتوازي:
T001, T002, T003

# Phase 2 — بعد T001:
T005, T006 بالتوازي ثم T007, T008

# US3 tests بالتوازي:
T019, T020, T021, T022

# US4 tests بالتوازي:
T028, T029, T030

# US5 + US6 tests بالتوازي (فرق مختلف):
T035–T037  و  T047–T049
```

---

## Implementation Strategy

### MVP First (US1 + US3)

1. Phase 1 + Phase 2
2. Phase 3 (US1) — ملخص مصدر الحقول
3. Phase 5 (US3) — ثقة الوحدة
4. **STOP & VALIDATE**: ملخص قبل السحب + pytest units
5. Demo للمستخدم

### Incremental Delivery

1. US1 + US2 → توثيق ومسار منظم
2. US3 + US4 → استنتاج أدق
3. US5 → تقرير مراجعة + سجل
4. US6 → قواعد تصنيف (اختياري)

### Suggested commit slices

1. `feat(mapping): field sources + pre-scrape summary UI`
2. `feat(units): UnitMatchResult with confidence`
3. `feat(brands): BrandMatchResult with confidence`
4. `feat(review): review report + run history`
5. `feat(rules): category mapping rules P3`

---

## Notes

- لا تغيير في أعمدة Excel الـ 29 — كل التحسينات metadata + UI
- `match_unit_for_category()` و`match_brand()` يبقيان للتوافق مع الاختبارات القديمة
- تطبيق `.app` يحتاج إعادة بناء بعد تغييرات `app/ui.py` و`pipeline/*`
- [P] tasks = ملفات مختلفة؛ تجنب تعديل `runner.py` من عدة مهام بالتوازي
