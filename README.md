# Product Scraper

سكريبت Python لسحب المنتجات والصور من مواقع التجارة الإلكترونية، مع تصدير البيانات إلى Excel.

## المخرجات

```
output_folder/
├── products.xlsx
└── product_images/
    ├── product_0001.jpg
    ├── product_0002.jpg
    └── ...
```

ملف Excel بصيغة استيراد جاهزة بالأعمدة:

`Id`, `Name`, `Description`, `Image`, `CategoryId`, `SubCategoryId`, `BrandId`, `UnitId`, `Stock`, `Price`, `Discount`, `DiscountType`, `AvailableTimeStarts`, `AvailableTimeEnds`, `Variations`, `ChoiceOptions`, `AddOns`, `Attributes`, `Tags`, `StoreId`, `ModuleId`, `Status`, `Veg`, `Recommended`, `IsDefaultProduct`, `IsPrescriptionReq`, `CommonConditions`, `IsBasic`, `QuantityUnit`

| العمود | المصدر |
|--------|--------|
| Id | SKU المنتج (أو رقم تسلسلي) |
| Name | اسم المنتج |
| Description | الوصف |
| Image | مسار الصورة مثل `product_images/product_0001.jpg` |
| Price | السعر |
| Tags | اسم الفئة المسحوبة |
| باقي الأعمدة | قيم افتراضية من `IMPORT_DEFAULTS` في `scraper.py` |

عدّل `IMPORT_DEFAULTS` في `scraper.py` لتعيين `CategoryId`, `SubCategoryId`, `StoreId`, `ModuleId`, `Stock`, وغيرها حسب نظامك.

## التثبيت

```bash
pip install -r requirements.txt
```

أو:

```bash
python3 -m pip install requests beautifulsoup4 openpyxl lxml
```

## الاستخدام

### سعودي سوبرماركت (GraphQL تلقائياً)

```bash
python scraper.py \
  --url "https://seoudisupermarket.com/ar/snacks-sweets/chips-dips-snacks?page=5" \
  --output output_folder \
  --max-pages 5
```

- يبدأ من الصفحة المحددة في الرابط (`page=5`).
- `--max-pages 5` يعني سحب 5 صفحات بدءاً من صفحة البداية.
- `--max-pages 0` يعني سحب كل الصفحات المتاحة.

### مواقع HTML عامة

```bash
python scraper.py --url "https://example.com/category" --output my_products --mode html
```

## أوضاع التشغيل

| الوضع | الوصف |
|-------|--------|
| `auto` (افتراضي) | يكتشف `seoudisupermarket.com` ويستخدم GraphQL، وإلا يستخدم HTML |
| `graphql` | فرض وضع GraphQL (Magento API) |
| `html` | سحب عبر BeautifulSoup و CSS selectors |

## ملاحظة مهمة عن سعودي سوبرماركت

موقع [seoudisupermarket.com](https://seoudisupermarket.com) مبني بـ **Nuxt.js/Vue** ولا يعرض المنتجات كاملة في HTML عند التحميل الأولي. لذلك:

- **السيليكتورات وحدها لا تكفي** على هذا الموقع.
- السكريبت يستخدم تلقائياً **Magento GraphQL** على `mcprod.seoudisupermarket.com/graphql`.
- حقل **الوصف** قد يكون فارغاً لكثير من المنتجات لأن API لا يعيد وصفاً.

## تعديل السيليكتورات (للمواقع HTML)

كل موقع له HTML مختلف. في `scraper.py` داخل قسم `SELECTORS`، عدّل السيليكتورات حسب الموقع:

1. افتح الموقع في Chrome.
2. كليك يمين على اسم المنتج ← **Inspect**.
3. انسخ الـ `class` المناسب.
4. ضعه في السيليكتور المناسب.

مثال: إذا كان اسم المنتج `<h1 class="item-title">` اكتب:

```python
"product_name": "h1.item-title",
```

### السيليكتورات المتاحة

| المفتاح | الغرض |
|---------|--------|
| `product_card` | بطاقة المنتج في صفحة الفئة |
| `product_link` | رابط المنتج داخل البطاقة |
| `product_name` | اسم المنتج في صفحة التفاصيل |
| `product_price` | السعر |
| `product_category` | الفئة (breadcrumb) |
| `product_description` | الوصف |
| `product_sku` | رقم SKU |
| `product_image` | صورة المنتج |
| `next_page` | رابط الصفحة التالية |

## إعدادات SETTINGS

| الإعداد | الافتراضي | الوصف |
|---------|-----------|--------|
| `delay_between_requests` | `1.5` | تأخير بين الطلبات (ثواني) |
| `max_pages` | `5` | أقصى عدد صفحات |
| `download_full_image` | `True` | محاولة جلب صورة أوضح بدون cache |
| `image_format` | `webp` | صيغة حفظ الصور (`webp` أو `original`) |
| `webp_quality` | `85` | جودة WebP من 1 إلى 100 |
| `images_folder` | `product_images` | مجلد الصور |
| `excel_filename` | `products.xlsx` | اسم ملف Excel |
| `graphql_page_size` | `20` | عدد المنتجات لكل صفحة في GraphQL |

## معاملات سطر الأوامر

| المعامل | مطلوب | الوصف |
|---------|-------|--------|
| `--url` | نعم | رابط صفحة الفئة |
| `--output` | لا | مجلد الإخراج (افتراضي: `output`) |
| `--max-pages` | لا | عدد الصفحات (0 = الكل) |
| `--mode` | لا | `auto` / `html` / `graphql` |

## تنبيه أخلاقي وقانوني

- احترم شروط استخدام الموقع.
- لا ترفع معدل الطلبات بشكل مفرط؛ استخدم `delay_between_requests` المناسب.
- استخدم البيانات للأغراض المسموح بها فقط.
