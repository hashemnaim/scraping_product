"""سحب إنستاشوب عبر Playwright."""

from __future__ import annotations

import re

from pipeline.constants import HEADERS, SCRAPE_SETTINGS

INSTASHOP_EXTRACT_JS = """
() => {
  const links = [...document.querySelectorAll('a[href*="/product/"]')];
  const seen = new Set();
  const items = [];
  for (const anchor of links) {
    const href = anchor.href;
    if (seen.has(href)) continue;
    seen.add(href);
    let root = anchor;
    for (let i = 0; i < 10; i++) {
      if (root.querySelector('.product-title') && root.querySelector('.price-txt')) break;
      root = root.parentElement;
      if (!root) break;
    }
    if (!root) root = anchor;
    const name = root.querySelector('.product-title')?.innerText?.trim() || '';
    const price = root.querySelector('.price-txt')?.innerText?.trim() || '';
    const packaging = root.querySelector('.product-packaging-string')?.innerText?.trim() || '';
    const img = root.querySelector('img');
    const id = href.split('/product/').pop().split('?')[0];
    if (!name) continue;
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


def _clean_price(raw: str) -> str:
    if not raw:
        return ""
    match = re.search(r"[\d]+(?:[.,]\d+)?", raw.replace(",", ""))
    return match.group(0) if match else raw.strip()


def scrape_instashop_category(url: str, on_progress=None) -> list[dict]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=SCRAPE_SETTINGS["instashop_headless"],
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            locale="ar-EG",
            viewport={"width": 1440, "height": 900},
            user_agent=HEADERS["User-Agent"],
        )
        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(10000)

        title = page.title()
        if "Cloudflare" in title or "Attention Required" in title:
            browser.close()
            raise RuntimeError("تم حظر الوصول من Cloudflare. جرّب instashop_headless=False")

        category_name = "مشروبات وعصاير"
        for selector in ["h1", ".category-title", "[class*='category'] h1"]:
            locator = page.locator(selector).first
            if locator.count():
                text = locator.inner_text(timeout=2000).strip()
                if text:
                    category_name = text
                    break

        prev_count = 0
        stable_rounds = 0
        for scroll_index in range(60):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(int(SCRAPE_SETTINGS["instashop_scroll_pause"] * 1000))
            count = page.evaluate(
                "() => new Set([...document.querySelectorAll('a[href*=\"/product/\"]')]"
                ".map(a => a.href)).size"
            )
            if on_progress:
                on_progress("scroll", scroll_index + 1, 60, f"{count} منتج")
            if count == prev_count:
                stable_rounds += 1
                if stable_rounds >= 3:
                    break
            else:
                stable_rounds = 0
            prev_count = count

        raw_items = page.evaluate(INSTASHOP_EXTRACT_JS)
        browser.close()

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
