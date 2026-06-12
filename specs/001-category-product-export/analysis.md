# Consistency Analysis: 001-category-product-export

**Date**: 2026-06-09  
**Artifacts reviewed**: spec.md, plan.md, tasks.md, data-model.md, research.md, contracts/, quickstart.md, checklist  
**Codebase**: `scraper.py`, `update_fruits_excel.py`, `README.md` (no `pipeline/` yet)

## Executive Summary

| Dimension | Status | Score |
|-----------|--------|-------|
| Spec ↔ Plan alignment | ✅ Strong | 95% |
| Spec ↔ Tasks coverage (FR) | ✅ Good | 91% |
| Plan ↔ Tasks structure | ✅ Aligned | 98% |
| Data model ↔ Contracts | ✅ Aligned | 97% |
| Codebase ↔ Spec | ❌ **Drift** | 35% |
| User-blocking dependencies | ⚠️ Open | 2 items |

**Verdict**: التصميم متسق وجاهز للتنفيذ مع **4 فجوات مهمة** في tasks و**انحراف كبير** في الكود الحالي. يُنصح بإصلاح المهام الناقصة ثم `/speckit.implement` من T001.

---

## 1. Functional Requirements Traceability

| FR | Description (short) | Task(s) | Status |
|----|---------------------|---------|--------|
| FR-001 | Excel 29 columns | T018, T028 | ✅ |
| FR-002 | Global Id sequence | T009, T026 | ✅ |
| FR-003 | Persist last_used_id | T009 | ✅ |
| FR-004 | WebP compression | T016 | ✅ |
| FR-005 | Image filename padding | T033 | ✅ |
| FR-006 | Image column path | T034 | ✅ |
| FR-007 | UI module/category pick | T021–T023 | ✅ |
| FR-008 | Central catalog config | T004, T007, T008, T050 | ✅ |
| FR-009 | Units per module only | T024, T037 | ✅ |
| FR-010 | Weight → UnitId | T037, T039 | ✅ |
| FR-011 | ModuleId from UI | T028, T026 | ✅ |
| FR-012 | Default import values | T040 | ✅ |
| FR-013 | Arabic Tags | T038, T039 | ✅ |
| FR-014 | Arabic Name | T041 | ✅ |
| FR-015 | Per-category output folder | T028, T030 | ✅ |
| FR-016 | Multi-source scrape | T012–T015, T046–T048 | ⚠️ Split across US2/US6 |
| FR-017 | Image filter by Excel | T042–T044 | ✅ |
| FR-018 | Image retry | T016 | ✅ |
| FR-019 | Scrape progress UI | T031, T036 | ⚠️ Partial — no mid-scrape progress task |
| FR-020 | URL/pages/output inputs | T030 | ✅ |
| FR-021 | Rescrape replace ids | T029, T032 | ⚠️ CLI only — **no UI rescrape** |
| FR-022 | Units from user xlsx | T025, T051, T011 | ✅ |

**Uncovered / weak**: FR-019 (live progress bar during pagination), FR-021 (UI toggle).

---

## 2. Success Criteria Traceability

| SC | Task coverage | Gap |
|----|---------------|-----|
| SC-001 | T021–T031 | — |
| SC-002 | T017, T033, T034 | — |
| SC-003 | T010 (partial) | **No integration test: two different categories** |
| SC-004 | T016 | **No validation/metric task for 80% compression** |
| SC-005 | T018 | — |
| SC-006 | T004, T021 | — |
| SC-007 | T025, T037 | — |

---

## 3. User Story ↔ Phase Consistency

| Story | Spec Priority | Tasks Phase | Match |
|-------|---------------|-------------|-------|
| US1 UI | P1 | Phase 3 | ✅ |
| US2 Scrape package | P1 | Phase 4 | ✅ |
| US3 WebP/images | P1 | Phase 5 | ✅ (mostly done in Phase 2 T016) |
| US4 Import data | P2 | Phase 6 | ✅ |
| US5 Image filter | P2 | Phase 7 | ✅ |
| US6 Multi-source | P2 | Phase 8 | ⚠️ Extraction in Phase 2; wiring split |

**Ordering note**: US3 tasks (T033–T036) largely extend T016 — acceptable but Phase 5 could merge into Phase 2 for efficiency.

---

## 4. Cross-Artifact Conflicts

### 4.1 🔴 Codebase vs Spec (Critical)

| Topic | spec/plan | Current `scraper.py` |
|-------|-----------|----------------------|
| Product `Id` | Global continuous | `product_id = index` from **1 per run** |
| Image format | WebP `product_{Id}.webp` | WebP but tied to **local index** |
| `ModuleId` | From UI/catalog | Hardcoded `"1"` in `IMPORT_DEFAULTS` |
| `CategoryId` | Per category | Empty / manual |
| Tags | Rich Arabic keywords | Category name only (README) |
| Output layout | `output/{slug}/` | User-defined folder only |

**Impact**: لا يمكن اعتبار الكود الحالي جزءاً من الميزة — إعادة الهيكلة إلزامية (كما في plan).

### 4.2 🟡 Task ordering: US2 before US6 wiring

- **T027** wires generic detector in US2.
- **T046** adds Seoudi `url_path` filter (required for fruits — worked around in old scraper).

**Risk**: MVP سحب فواكه سعودي قد يفشل إذا نُفّذ T027 دون T046.

**Fix**: نقل T046 إلى Phase 4 (قبل أو مع T027) أو دمج `url_path` في T012.

### 4.3 🟡 Spec says catalog editable from UI

Spec (Module Catalog): «قابل للتعديل من الواجهة أو ملف JSON».

Tasks: فقط T050 يدوي في JSON — **لا مهمة لتحرير الكتالوج من الواجهة**.

**Severity**: Medium — يمكن تأجيله لما بعد MVP إذا وُثّق في Out of Scope.

### 4.4 🟢 Clarifications ↔ Design

| Clarification | Reflected in plan/tasks? |
|---------------|--------------------------|
| Rescrape = replace ids | T009, T029 ✅ |
| Modules 7–8 reserved | T004, T021 ✅ |
| Units from user xlsx | T051, T005 seed ✅ |

---

## 5. Data Model ↔ Contracts ↔ Tasks

| Entity | data-model.md | contracts | tasks |
|--------|---------------|-----------|-------|
| GlobalIdState | ✅ | global-state.schema.json | T009 |
| CategoryRun | ✅ | category-run.schema.json | T019, T026 |
| `freed_ids` on shrink | ✅ | schema has field | ⚠️ T009 text omits `freed_ids` |
| run_key format | `{m}/{cat}/{sub}` | pipeline-service.md | T009 (implicit) |

**Minor gap**: أضف صراحةً `freed_ids` إلى T009.

---

## 6. External Dependencies (User)

| Dependency | Spec | Tasks | Blocker? |
|------------|------|-------|----------|
| `catalog/units.xlsx` | Required for all modules | T051; seed for mod 2 only | Blocks modules 1,3–6 |
| `catalog/categories.json` full IDs | Required | T007 skeleton, T050 | Blocks non-fruits categories |
| User category ID table | Mentioned | T050 only | **Needs user input** |

---

## 7. Documentation Drift

| File | Issue |
|------|-------|
| `README.md` | JPG naming, SKU as Id, no Streamlit, no global ids |
| `quickstart.md` | ✅ Aligned with plan |
| `checklists/requirements.md` | ✅ Complete |

T052 addresses README — keep after implement or do early to avoid confusion.

---

## 8. Recommended Task Amendments

Add before `/speckit.implement`:

| ID | Suggested task |
|----|----------------|
| **T055** | [US2] Add «إعادة سحب» checkbox in `app/ui.py` passing `rescrape=true` to `run_category_job()` |
| **T056** | [US2] Add `on_progress` callback wiring (phase, current/total) in `app/ui.py` during scrape (FR-019) |
| **T057** | Move Seoudi `url_path` integration from T046 into T012 or execute T046 before T027 MVP test |
| **T058** | [P] Add `tests/integration/test_two_category_ids.py` asserting SC-003 contiguous global ids |
| **T059** | [P] Optional: log compression ratio in `pipeline/images.py` stats for SC-004 manual check |

Optional defer to post-MVP:

- UI catalog editor (spec «قابل للتعديل من الواجهة»)

---

## 9. Terminology Consistency

| Term | spec | plan | tasks | Consistent |
|------|------|------|-------|------------|
| ModuleId 1–6 active | ✅ | ✅ | ✅ | ✅ |
| `global_state.json` path | data/ | data/ | data/ | ✅ |
| `product_{Id}.webp` | ✅ | ✅ | ✅ | ✅ |
| `units.seed.json` | implied | ✅ | T005 | ✅ |
| `run_key` | data-model | contracts | implicit | ✅ |

---

## 10. Implementation Readiness Checklist

- [x] Spec complete, clarifications resolved
- [x] Plan + research + data model + contracts
- [x] Tasks ordered with MVP defined (T001–T032)
- [ ] User `units.xlsx` — **pending**
- [ ] Full `categories.json` — **pending user IDs**
- [ ] Task gaps T055–T058 — **recommended**
- [ ] Code refactor not started (`pipeline/` missing)

---

## 11. Suggested Next Steps

1. **Accept or add** tasks T055–T058 to `tasks.md`.
2. **Provide** `catalog/units.xlsx` and category ID table (or start MVP on module 2 only).
3. Run **`/speckit.implement`** Phase 1–2 then US1–US2.
4. Update **`README.md`** early (T052) to reduce spec/code confusion during refactor.

**Overall**: Analysis **PASS with conditions** — design artifacts are consistent; implementation has not started; codebase requires full pipeline migration.
