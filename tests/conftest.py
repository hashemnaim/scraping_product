"""إعداد pytest — تثبيت Playwright تلقائياً إن لم يكن موجوداً."""

from __future__ import annotations


def pytest_sessionstart(session) -> None:
    try:
        from pipeline.scrape.playwright_bootstrap import ensure_playwright_chromium

        ensure_playwright_chromium()
    except Exception:
        # اختبارات الوحدة لا تحتاج متصفحاً؛ نتجاهل الفشل هنا.
        pass
