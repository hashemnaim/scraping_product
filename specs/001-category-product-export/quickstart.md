# Quickstart: نظام تصدير المنتجات

**Branch**: `001-category-product-export`

## المتطلبات

- Python 3.11+
- macOS (مُختبر) أو Linux

## التثبيت

```bash
cd /Users/mac/Desktop/scripngproducet
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## إعداد الكتالوج

```bash
# بعد التنفيذ — الملفات المتوقعة:
catalog/modules.json       # الموديلات 1–6
catalog/categories.json    # التصنيفات والمعرفات
catalog/units.xlsx         # من المستخدم (أو units.seed.json لموديل 2 مؤقتاً)
data/global_state.json     # يُنشأ تلقائياً { "last_used_id": 0, ... }
```

### نموذج `units.xlsx`

| ModuleId | UnitId | NameAr | Aliases |
|----------|--------|--------|---------|
| 2 | 2 | كيلو | kg,كجم,كيلو |
| 2 | 3 | غرام | g,جم,غرام |

## تشغيل الواجهة (بعد التنفيذ)

```bash
streamlit run app/ui.py
```

1. اختر **الموديل** (مثل خضروات وفواكه).
2. اختر **التصنيف الرئيسي** ثم **الفرعي** — تُعبَّأ المعرفات تلقائياً.
3. أدخل **رابط المصدر** ومجلد الإخراج.
4. اضغط **بدء السحب** — راقب التقدم والصور.

## CLI (توافق مع السكريبت الحالي)

```bash
python scraper.py --url "https://seoudisupermarket.com/ar/..." \
  --output output/fruits \
  --excel-filename fruits.xlsx \
  --images-folder fruits_images \
  --module-id 2 --category-id 253 --sub-category-id 10 \
  --max-pages 0
```

## إعادة سحب تصنيف (استبدال المعرفات)

```bash
python scraper.py ... --rescrape
# أو من الواجهة: تفعيل "إعادة سحب هذا التصنيف"
```

## تصفية الصور

```bash
python -m pipeline.images filter \
  --excel output/fruits/fruits.xlsx \
  --images output/fruits/fruits_images
```

## التحقق السريع

- `Id` في Excel يطابق رقم الصورة (`product_086.webp` ↔ Id=86).
- تصنيفان متتاليان: أول Id في الثاني = آخر Id في الأول + 1.
- `ModuleId` / `CategoryId` / `SubCategoryId` تطابق اختيار الواجهة.

## المخرجات

```text
output/{slug}/
├── {excel_filename}.xlsx
└── {images_folder}/
    ├── product_001.webp
    └── ...
data/global_state.json   # الترقيم العالمي
```
