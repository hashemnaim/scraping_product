# Research: توثيق ودقة ربط حقول التصدير

**Branch**: `002-catalog-field-mapping` | **Date**: 2026-06-15

## R1 — مصدر حقول Excel في النظام الحالي

**Decision**: فصل واضح بين ثلاث طبقات مصدر:

| الحقل | المصدر الفعلي اليوم | ملف/مكوّن |
|-------|---------------------|-----------|
| `ModuleId`, `CategoryId`, `SubCategoryId` | اختيار المستخدم في `app/ui.py` | `catalog.py` |
| `Name`, `Price`, `Image` | السحب من المصدر | `scrape/*` |
| `UnitId`, `QuantityUnit` | استنتاج من `product.name` | `units_matcher.py` |
| `BrandId` | استنتاج من `product.name` | `brand_matcher.py` |
| `Tags` | توليد من الاسم + التصنيف المختار | `tags.py` |

**Rationale**: الموقع المصدر لا يوفّر معرفات كتالوج المستخدم؛ محاولة «قراءة» CategoryId من HTML ستكون هشة وغير قابلة للصيانة.

**Alternatives considered**:
- *ربط تلقائي بمعرفات الموقع*: مرفوض — كل موقع له مخطط مختلف.
- *تصنيف فرعي بالذكاء الاصطناعي*: خارج النطاق؛ قد يُدرَج لاحقاً.

---

## R2 — قواعد الوحدة حسب التصنيف

**Decision**: الإبقاء على `category_allows_weight_units()` — خضروات/فواكه/أجبان تحتفظ بغرام/كيلو/مل؛ غير ذلك → قطعة + 1 عبر `finalize_unit_for_export()`.

**Rationale**: مطابق لسياسة العمل المتفق عليها في 001 ومُختبر في `test_units_matcher.py`.

**Alternatives considered**:
- *السماح بالمل في كل التصنيفات*: مرفوض — يخلط سعر القطعة مع الحجم في سوبرماركت.

---

## R3 — كيف نُعلم المستخدم قبل السحب؟

**Decision**: لوحة ملخص ثابتة في Streamlit (ليست modal) تعرض:
1. جدول مصادر الحقول
2. القيم المختارة حالياً (Module/Category/SubCategory)
3. نصيحة مسار العمل: رابط واحد = تصنيف فرعي واحد

**Rationale**: المستخدم غير تقني؛ لا يحتاج قراءة spec — يحتاج إجابة قبل الضغط على «بدء السحب».

**Alternatives considered**:
- *PDF منفصل*: مرفوض — خارج التطبيق.
- *Tooltip فقط*: ضعيف — لا يكفي لـ SC-001.

---

## R4 — تقرير المراجعة بعد السحب

**Decision**: بناء `ReviewReport` في الذاكرة أثناء `run_category_job` دون ملف منفصل إلزامي؛ العرض في UI؛ اختياري تصدير JSON بجانب Excel.

**Warning types**:
- `default_unit` — اعتمدت قطعة/1 بدون مؤشر واضح في الاسم
- `ambiguous_unit` — أكثر من نمط وحدة في الاسم (مثل 6×500مل)
- `missing_brand` — لا مطابقة في brands.csv
- `missing_price` — سعر فارغ
- `failed_image` — `image_ok=false`
- `category_rule_applied` — (P3) تغيّر SubCategoryId عن اختيار المستخدم

**Rationale**: يحقق FR-015/FR-016 وSC-005 دون تغيير أعمدة Excel.

---

## R5 — قواعد ربط تصنيف المصدر (P3)

**Decision**: ملف `catalog/category_mapping_rules.xlsx` بقواعد نصية (contains/equals) مرتبة بـ `priority`؛ الاحتياطي = `sub_category_id` من الواجهة.

**Rationale**: يغطي صفحات مختلطة التصنيف دون إجبار المستخدم على قواعد معقدة في الكود.

**Alternatives considered**:
- *Regex في JSON*: أصعب على المستخدم غير التقني — Excel أوضح.
- *قاعدة واحدة لكل موقع في detector*: صلبة — ملف كتالوج أمرن.

---

## R6 — سجل التشغيل

**Decision**: `data/run_history.jsonl` — سطر JSON لكل عملية: وقت، run_key، source_url، products_total، معدلات التحذيرات.

**Rationale**: FR-018؛ يساعد على قياس SC-006 قبل/بعد.

---

## R7 — تغييرات الواجهة والتطبيق المجمّع

**Decision**: لا تغيير في PyInstaller spec إلا إضافة `hiddenimports` لملفات pipeline الجديدة عند البناء.

**Rationale**: الميزة UI + pipeline فقط؛ نفس مسار `ScrapingProduct-M1.app`.
