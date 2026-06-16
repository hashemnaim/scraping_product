"""سحب محلات من Google Maps عبر Playwright."""

from __future__ import annotations

import re
import urllib.parse

from pipeline.constants import HEADERS, SCRAPE_SETTINGS
from pipeline.scrape.playwright_bootstrap import ensure_playwright_chromium

_LIST_EXTRACT_JS = """
() => {
  const feed = document.querySelector('div[role="feed"]');
  if (!feed) return [];
  const seen = new Set();
  const items = [];
  for (const link of feed.querySelectorAll('a[href*="/maps/place/"]')) {
    const href = (link.href || '').split('?')[0];
    if (!href || seen.has(href)) continue;
    seen.add(href);
    const card = link.closest('div.Nv2PK') || link.closest('[jsaction]') || link.parentElement;
    const name = (link.getAttribute('aria-label') || link.textContent || '').trim();
    let address = '';
    if (card) {
      const spans = [...card.querySelectorAll('span')]
        .map((el) => (el.textContent || '').trim())
        .filter((text) => text && text !== name);
      address = spans.find((text) => text.length > 8) || spans[0] || '';
    }
    items.push({ name, address, url: href });
  }
  return items;
}
"""

_PHONE_EXTRACT_JS = """
() => {
  const tel = document.querySelector('a[href^="tel:"]');
  if (tel) return tel.getAttribute('href').replace('tel:', '').trim();
  const phoneBtn = document.querySelector('button[data-item-id^="phone"]');
  if (phoneBtn) {
    const label = phoneBtn.getAttribute('aria-label') || phoneBtn.textContent || '';
    const match = label.match(/[\\d+][\\d\\s\\-()]{6,}/);
    return match ? match[0].trim() : label.trim();
  }
  const copyPhone = document.querySelector('[data-tooltip*="phone" i], [aria-label*="هاتف" i]');
  if (copyPhone) {
    const label = copyPhone.getAttribute('aria-label') || copyPhone.textContent || '';
    const match = label.match(/[\\d+][\\d\\s\\-()]{6,}/);
    return match ? match[0].trim() : '';
  }
  return '';
}
"""


def _clean_phone(raw: str) -> str:
    if not raw:
        return ""
    digits = re.sub(r"[^\d+]", "", raw)
    return digits or raw.strip()


def _search_url(category: str, city: str, district: str = "") -> str:
    area = " ".join(part for part in (district.strip(), city.strip()) if part)
    query = f"{category} في {area}".strip()
    encoded = urllib.parse.quote(query)
    return f"https://www.google.com/maps/search/{encoded}"


def _scroll_rounds_for_radius(radius_km: float) -> int:
    return max(8, min(40, int(radius_km * 1.8)))


def _launch_context(playwright):
    browser = playwright.chromium.launch(
        headless=SCRAPE_SETTINGS["instashop_headless"],
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ],
    )
    context = browser.new_context(
        locale="ar-EG",
        timezone_id="Africa/Cairo",
        viewport={"width": 1440, "height": 900},
        user_agent=HEADERS.get("User-Agent"),
        extra_http_headers={
            "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    page = context.new_page()
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
    )
    return browser, page


def _scroll_results(page, rounds: int, on_progress=None) -> None:
    stable = 0
    prev_count = 0
    for index in range(rounds):
        page.evaluate(
            """
            () => {
              const feed = document.querySelector('div[role="feed"]');
              if (feed) feed.scrollTop = feed.scrollHeight;
            }
            """
        )
        page.wait_for_timeout(1200)
        count = page.evaluate(
            "() => document.querySelectorAll('a[href*=\"/maps/place/\"]').length"
        )
        if on_progress:
            on_progress("maps_scroll", index + 1, rounds, f"{count} محل")
        if count == prev_count:
            stable += 1
            if stable >= 3 and count > 0:
                break
        else:
            stable = 0
        prev_count = count


def _enrich_phone(page, url: str) -> str:
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1800)
        raw = page.evaluate(_PHONE_EXTRACT_JS)
        return _clean_phone(raw or "")
    except Exception:
        return ""


def scrape_maps_places(
    city: str,
    radius_km: float,
    categories: list[str],
    district: str = "",
    on_progress=None,
) -> list[dict]:
    if not city.strip():
        raise ValueError("المدينة مطلوبة")
    if not categories:
        raise ValueError("اختر تصنيفاً واحداً على الأقل")

    ensure_playwright_chromium()
    from playwright.sync_api import sync_playwright

    all_places: list[dict] = []
    seen_urls: set[str] = set()

    with sync_playwright() as playwright:
        browser, page = _launch_context(playwright)
        scroll_rounds = _scroll_rounds_for_radius(radius_km)

        for cat_index, category in enumerate(categories, start=1):
            if on_progress:
                on_progress(
                    "maps_category",
                    cat_index,
                    len(categories),
                    f"جاري سحب: {category}",
                )
            page.goto(_search_url(category, city, district), wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3000)

            title = page.title().lower()
            if "sorry" in title or "captcha" in title:
                browser.close()
                raise RuntimeError(
                    "تعذّر الوصول إلى Google Maps (حظر أو Captcha). "
                    "جرّب لاحقاً أو قلّل عدد التصنيفات."
                )

            try:
                page.wait_for_selector('div[role="feed"]', timeout=20000)
            except Exception:
                continue

            _scroll_results(page, scroll_rounds, on_progress)
            raw_items = page.evaluate(_LIST_EXTRACT_JS)

            for item_index, item in enumerate(raw_items, start=1):
                url = (item.get("url") or "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                name = (item.get("name") or "").strip()
                if not name:
                    continue
                phone = _enrich_phone(page, url)
                all_places.append(
                    {
                        "name": name,
                        "address": (item.get("address") or "").strip(),
                        "phone": phone,
                        "category": category,
                        "city": city.strip(),
                        "coverage_km": radius_km,
                        "maps_url": url,
                    }
                )
                if on_progress and item_index % 5 == 0:
                    on_progress("maps_place", len(all_places), 0, name[:40])

        browser.close()

    return all_places
