"""
Product Scraper — غلاف CLI يستدعي pipeline.run_category_job

الاستخدام:
    python scraper.py --url "https://seoudisupermarket.com/ar/fruits-vegetables-2/fruits" \\
        --output output --module-id 2 --category-id 253 --sub-category-id 10 \\
        --excel-filename fruits.xlsx --max-pages 0
"""

import argparse
import sys

from pipeline.errors import PipelineError
from pipeline.runner import CategoryRunRequest, run_category_job
from pipeline.scrape.detector import detect_mode


def main():
    parser = argparse.ArgumentParser(description="سكريبت سحب المنتجات (Pipeline)")
    parser.add_argument("--url", required=True, help="رابط صفحة الفئة")
    parser.add_argument("--output", default="output", help="مجلد الإخراج الجذر")
    parser.add_argument("--module-id", type=int, required=True, help="معرف الموديل (1-6)")
    parser.add_argument("--category-id", type=int, required=True, help="CategoryId")
    parser.add_argument("--sub-category-id", type=int, required=True, help="SubCategoryId")
    parser.add_argument("--max-pages", type=int, default=0, help="0 = كل الصفحات")
    parser.add_argument("--excel-filename", default="products.xlsx")
    parser.add_argument(
        "--mode",
        choices=["auto", "html", "graphql", "instashop"],
        default="auto",
    )
    parser.add_argument("--rescrape", action="store_true", help="إعادة سحب بنفس نطاق المعرفات")
    parser.add_argument(
        "--excel-only",
        action="store_true",
        help="تصدير Excel فقط بدون تحميل الصور",
    )
    parser.add_argument(
        "--apply-category-rules",
        action="store_true",
        help="تطبيق catalog/category_mapping_rules.xlsx على SubCategoryId",
    )
    args = parser.parse_args()

    if detect_mode(args.url, args.mode) == "instashop":
        from pipeline.scrape.playwright_bootstrap import ensure_playwright_chromium

        print("⏳ تجهيز متصفح Instashop (headless)...")
        ensure_playwright_chromium()

    request = CategoryRunRequest(
        module_id=args.module_id,
        category_id=args.category_id,
        sub_category_id=args.sub_category_id,
        source_url=args.url,
        output_dir=args.output,
        excel_filename=args.excel_filename,
        max_pages=args.max_pages,
        rescrape=args.rescrape,
        mode=args.mode,
        apply_category_rules=args.apply_category_rules,
        excel_only=args.excel_only,
    )

    def on_progress(phase, current, total, message):
        print(f"  [{phase}] {current}/{total} {message}")

    try:
        print(f"\n🚀 بدء السحب: {args.url}\n")
        result = run_category_job(request, on_progress=on_progress)
        print(f"\n✨ اكتمل!")
        print(f"   Excel: {result.excel_path}")
        print(f"   صور: {result.images_dir}")
        print(f"   Id: {result.id_range['start']} — {result.id_range['end']}")
        print(f"   إحصائيات: {result.stats}")
    except PipelineError as exc:
        print(f"\n❌ {exc.code}: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"\n❌ {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
