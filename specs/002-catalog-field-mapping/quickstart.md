# Quickstart: توثيق ودقة ربط حقول التصدير

**Branch**: `002-catalog-field-mapping`

## مسار العمل المنظم (موصى به)

```
1. اختر الموديل → التصنيف الرئيسي → التصنيف الفرعي في الواجهة
2. أدخل رابط صفحة واحدة فقط لهذا التصنيف الفرعي
3. اقرأ «ملخص حقول Excel» قبل الضغط على بدء السحب
4. شغّل السحب
5. راجع «تقرير المراجعة» — صحّح الكتالوج أو أعد السحب إن لزم
6. استورد Excel
```

**قاعدة ذهبية**: رابط واحد = تصنيف فرعي واحد.

---

## من أين يأتي كل حقل؟

| حقل Excel | المصدر |
|-----------|--------|
| CategoryId / SubCategoryId | اختيارك في الواجهة |
| Name / Price / Image | الموقع |
| UnitId / QuantityUnit | اسم المنتج + وحدات الموديل |
| BrandId | اسم المنتج + brands.csv |

معرفات الموقع المصدر **لا تُستخدم** في Excel.

---

## التطوير المحلي

```bash
cd /Users/mac/Desktop/scripngproducet
./run_ui.sh
```

بعد تنفيذ الميزة:
- قبل السحب: expander «كيف تُملأ حقول Excel؟»
- بعد السحب: قسم «تقرير المراجعة»

---

## الاختبارات

```bash
.venv/bin/python -m pytest tests/unit/test_field_mapping.py tests/unit/test_review_report.py tests/unit/test_units_matcher.py tests/unit/test_brand_matcher.py -q
```

عينات SC-002 (وحدات):

| اسم المنتج | التصنيف | UnitId المتوقع | QuantityUnit |
|------------|---------|----------------|--------------|
| طماطم 1 كيلو | خضروات | كيلو | 1 |
| حليب 500 مل | سوبرماركت | قطعة | 1 |
| جبنة 250 غرام | أجبان | غرام | 250 |
| عرض خاص | أي | قطعة | 1 + تحذير |

---

## ملفات الكتالوج

| ملف | الغرض |
|-----|--------|
| `catalog/units.xlsx` | معرفات الوحدات لكل موديل |
| `catalog/brands.csv` | العلامات التجارية |
| `catalog/brand_aliases.csv` | مرادفات (pepsi → بيبسي) |
| `catalog/category_mapping_rules.xlsx` | (P3) ربط نص تصنيف الموقع → SubCategoryId |

---

## سجل التشغيل

بعد كل سحب:

```
data/run_history.jsonl
```

أو في التطبيق المجمّع:

```
~/Library/Application Support/ScrapingProduct/data/run_history.jsonl
```

---

## إعادة بناء تطبيق Mac M1

```bash
./scripts/build_mac_m1.sh
```
