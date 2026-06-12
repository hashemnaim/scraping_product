# Research: نظام تصدير المنتجات تصنيفاً بتصنيف

**Branch**: `001-category-product-export` | **Date**: 2026-06-09

## R1: واجهة المستخدم البسيطة

**Decision**: Streamlit (`streamlit`) كواجهة ويب محلية فوق منطق السحب الموجود.

**Rationale**:
- المشروع حالياً Python بالكامل (`scraper.py`، `openpyxl`، `playwright`).
- Streamlit يوفّر قوائم متتابعة (موديل → تصنيف → فرعي)، أزرار تشغيل، وشريط تقدم بأقل كود.
- لا يحتاج frontend منفصل (React) ولا خادم API معقد للمرحلة الأولى.
- يعمل محلياً على macOS (بيئة المستخدم).

**Alternatives considered**:
| البديل | سبب الرفض |
|--------|-----------|
| Tkinter | أقل جمالاً؛ صعوبة عرض التقدم والجداول |
| Flask + HTML | أكثر كوداً لنفس النتيجة |
| Gradio | مناسب لكن Streamlit أوضح لنماذج اختيار متعددة الخطوات |
| Electron | مبالغة في التعقيد |

---

## R2: هيكلة الكود (من `scraper.py` أحادي إلى حزمة)

**Decision**: إعادة هيكلة تدريجية إلى حزمة `pipeline/` مع الإبقاء على `scraper.py` كغلاف CLI للتوافق.

**Rationale**:
- `scraper.py` (~840 سطر) يجمع GraphQL سعودي، Instashop/Playwright، HTML، Excel، صور.
- فصل: `scrape/` (مصادر)، `exporter.py` (Excel)، `images.py` (WebP)، `id_state.py`، `catalog.py`.
- يسمح للواجهة وCLI باستدعاء `pipeline.run_category_job()` واحدة.

**Alternatives considered**:
- إبقاء ملف واحد: يصعب اختبار الترقيم العالمي والكتالوج.
- مشروعين منفصلين (API + UI): يخالف مبدأ البساطة للمستخدم الواحد.

---

## R3: ملف الحالة والترقيم العالمي

**Decision**: `data/global_state.json` يخزن `last_used_id` و`category_ranges` (مفتاح: `moduleId/categoryId/subCategoryId`).

**Rationale**:
- متطلبات المواصفة: تسلسل عالمي + إعادة سحب بنفس النطاق (استبدال).
- JSON بسيط، قابل للقراءة والنسخ الاحتياطي، لا يحتاج قاعدة بيانات.
- عند إعادة السحب: قراءة `id_start` للتصنيف، حذف صور النطاق القديم، كتابة Excel جديد.

**Alternatives considered**:
- SQLite: أقوى لكن زائد لملفات محلية فقط.
- معرفات داخل Excel فقط: لا يضمن التواصل بين تصنيفات متعددة.

---

## R4: كتالوج الموديلات والتصنيفات والوحدات

**Decision**:
- `catalog/modules.json` — الموديلات 1–6 (7–8 `active: false`).
- `catalog/categories.json` — شجرة `CategoryId` / `SubCategoryId` لكل موديل.
- `catalog/units.xlsx` — ملف المستخدم (مصدر الحقيقة للوحدات)؛ تحميل عبر `openpyxl`.
- `catalog/units.seed.json` — افتراضيات موديل 2 فقط (كيلو=2، غرام=3) حتى رفع الملف.

**Rationale**:
- المواصفة: معرفات مسبقة + وحدات من ملف المستخدم.
- JSON للكتالوج الثابت؛ Excel للوحدات لأن المستخدم اختار توفير جدول.
- رفض السحب إذا `units.xlsx` ناقص للموديل المختار (FR-022).

**Alternatives considered**:
- كل شيء في Excel واحد: أصعب صيانة للتصنيفات الهرمية.
- قاعدة بيانات: خارج النطاق.

---

## R5: معالجة الصور WebP

**Decision**: الإبقاء على Pillow (`Image.save(..., "WEBP", quality=85)`) مع تسمية `product_{id:0{width}d}.webp` حيث `width = max(3, len(str(id)))`.

**Rationale**:
- مُطبَّق ويعمل في `scraper.py` الحالي.
- يحقق SC-004 ويطابق `Id` عالمياً حتى >999.

**Alternatives considered**:
- `cwebp` CLI: تبعية نظام إضافية.
- AVIF: أقل توافقاً مع أنظمة الاستيراد الحالية.

---

## R6: مصادر السحب

**Decision**: الإبقاء على ثلاثة محركات مع كشف تلقائي:

| المصدر | الآلية |
|--------|--------|
| seoudisupermarket.com | GraphQL Magento |
| instashop.com | Playwright (non-headless افتراضياً) |
| أخرى | BeautifulSoup + `SELECTORS` |

**Rationale**: مُختبر في المشروع الحالي؛ المواصفة FR-016.

---

## R7: تصفية الصور

**Decision**: أمر/زر في الواجهة يقرأ عمود `Image` من Excel مرجعي، يبقي الملفات المذكورة، ينقل الباقي إلى `{images_folder}_removed/`.

**Rationale**: مطابق User Story 5 والعمل السابق (فواكه 28 منتج).

---

## R8: الاختبار

**Decision**: `pytest` لوحدات `id_state`، `catalog`، `images`، `exporter`؛ اختبار تكامل واحد بـ mock HTTP (بدون سحب حي في CI).

**Rationale**: الدستور غير مُفعَّل؛ اختبارات وحدة للمنطق الحرج (ترقيم، تسمية صور) كافية للمرحلة الأولى.

---

## R9: ملف الوحدات (تبعية المستخدم)

**Decision**: البدء بموديل خضروات وفواكه بـ `units.seed.json`؛ باقي الموديلات تتطلب `catalog/units.xlsx` من المستخدم.

**Rationale**: المواصفة تسجل «بانتظار رفع الملف»؛ لا نُخمّن معرفات وحدات الموديلات الأخرى.

**Status**: غير محجوب للتخطيط؛ محجوب لتشغيل موديلات 1، 3–6 حتى رفع الملف.
