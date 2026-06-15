"""سحب إنستاشوب عبر Playwright."""

from __future__ import annotations

import re

from pipeline.constants import HEADERS, SCRAPE_SETTINGS
from pipeline.scrape.playwright_bootstrap import ensure_playwright_chromium

_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

_STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['ar-EG', 'ar', 'en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = { runtime: {} };
"""

INSTASHOP_EXTRACT_JS = """
() => {
  const items = [];
  const seen = new Set();
  const cards = document.querySelectorAll('.product');
  for (const root of cards) {
    const name = root.querySelector('.product-title')?.innerText?.trim() || '';
    if (!name) continue;
    const price = root.querySelector('.price-txt')?.innerText?.trim() || '';
    const packaging = root.querySelector('.product-packaging-string')?.innerText?.trim() || '';
    const anchor = root.querySelector('a[href*="/product/"]');
    const href = anchor?.href || '';
    const id = href ? href.split('/product/').pop().split('?')[0] : name;
    const key = href || name;
    if (seen.has(key)) continue;
    seen.add(key);
    const img = root.querySelector('img');
    items.push({
      id,
      name,
      price,
      packaging,
      image: img?.src || img?.getAttribute('data-src') || '',
      url: href,
    });
  }
  return items;
}
"""

_PRODUCT_COUNT_JS = "() => document.querySelectorAll('.product-title').length"

_BLOCK_MARKERS = (
    "cloudflare",
    "attention required",
    "you have been blocked",
    "unable to access instashop",
    "sorry, you have been blocked",
)


def _clean_price(raw: str) -> str:
    if not raw:
        return ""
    match = re.search(r"[\d]+(?:[.,]\d+)?", raw.replace(",", ""))
    return match.group(0) if match else raw.strip()


def _launch_args() -> list[str]:
    args = ["--disable-blink-features=AutomationControlled"]
    if SCRAPE_SETTINGS["instashop_headless"]:
        args.extend(["--no-sandbox", "--disable-dev-shm-usage"])
    return args


def _dismiss_cookie_banner(page) -> None:
    for selector in (
        'button:has-text("Accept")',
        'button:has-text("قبول")',
        'button:has-text("Necessary only")',
    ):
        try:
            button = page.locator(selector).first
            if button.count() and button.is_visible(timeout=1500):
                button.click(timeout=2000)
                page.wait_for_timeout(800)
                return
        except Exception:
            continue


def _page_blocked(title: str, body_text: str) -> bool:
    haystack = f"{title}\n{body_text}".lower()
    return any(marker in haystack for marker in _BLOCK_MARKERS)


def _raise_if_blocked(page) -> None:
    title = page.title()
    body_text = page.evaluate("() => document.body?.innerText || ''")[:500]
    if _page_blocked(title, body_text):
        raise RuntimeError(
            "Instashop حجب الطلب (Cloudflare). "
            "جرّب السحب محلياً عبر ./run_ui.sh أو من IP غير السحابة."
        )


def _wait_for_products(page, timeout_ms: int = 90000) -> int:
    try:
        page.wait_for_function(
            "() => document.querySelectorAll('.product-title').length > 0",
            timeout=timeout_ms,
        )
    except Exception:
        pass
    return page.evaluate(_PRODUCT_COUNT_JS)


def _scroll_products(page, on_progress=None) -> None:
    prev_count = 0
    stable_rounds = 0
    pause_ms = int(SCRAPE_SETTINGS["instashop_scroll_pause"] * 1000)

    for scroll_index in range(60):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(pause_ms)
        count = page.evaluate(_PRODUCT_COUNT_JS)
        if on_progress:
            on_progress("scroll", scroll_index + 1, 60, f"{count} منتج")
        if count == prev_count:
            stable_rounds += 1
            # لا تتوقف مبكراً عند 0 — Instashop يحمّل المنتجات ببطء
            if count > 0 and stable_rounds >= 3:
                break
        else:
            stable_rounds = 0
        prev_count = count


def scrape_instashop_category(url: str, on_progress=None) -> list[dict]:
    ensure_playwright_chromium()
    from playwright.sync_api import sync_playwright

    user_agent = HEADERS.get("User-Agent") or _CHROME_UA

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=SCRAPE_SETTINGS["instashop_headless"],
            args=_launch_args(),
        )
        context = browser.new_context(
            locale="ar-EG",
            timezone_id="Africa/Cairo",
            viewport={"width": 1440, "height": 900},
            user_agent=user_agent,
            extra_http_headers={
                "Accept-Language": HEADERS.get("Accept-Language", "ar,en;q=0.9"),
                "Accept": HEADERS.get(
                    "Accept",
                    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                ),
                "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            },
        )
        page = context.new_page()
        page.add_init_script(_STEALTH_INIT_SCRIPT)
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
        _dismiss_cookie_banner(page)
        _raise_if_blocked(page)

        product_count = _wait_for_products(page)
        if product_count == 0:
            page.wait_for_timeout(8000)
            _raise_if_blocked(page)
            product_count = _wait_for_products(page, timeout_ms=30000)

        category_name = "غير مصنف"
        for selector in ["h1", ".category-title", "[class*='category'] h1"]:
            locator = page.locator(selector).first
            if locator.count():
                text = locator.inner_text(timeout=2000).strip()
                if text:
                    category_name = text
                    break

        _scroll_products(page, on_progress)
        raw_items = page.evaluate(INSTASHOP_EXTRACT_JS)
        browser.close()

    if not raw_items:
        raise RuntimeError(
            "لم يُعثر على منتجات في Instashop. "
            "قد يكون الرابط فارغاً أو الصفحة لم تُحمَّل (حظر Cloudflare على السحابة). "
            "جرّب نفس الرابط محلياً."
        )

    products = []
    for item in raw_items:
        products.append(
            {
                "name": item.get("name", ""),
                "price": _clean_price(item.get("price", "")),
                "category": category_name,
                "description": item.get("packaging", ""),
                "sku": item.get("id", ""),
                "image_url": item.get("image", ""),
                "product_url": item.get("url", ""),
            }
        )
    return products
