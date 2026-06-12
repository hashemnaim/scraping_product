"""سحب HTML عام عبر BeautifulSoup."""

from __future__ import annotations

import random
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from pipeline.constants import HEADERS, SCRAPE_SETTINGS

SELECTORS = {
    "product_card": "div.product-item, article.product, .product-card, li.product",
    "product_link": "a[href]",
    "product_name": "h1.product-title, h1.product__title, h1[class*='title'], .product-name h1",
    "product_price": (
        ".price, .product-price, "
        "[class*='price']:not([class*='old']):not([class*='original'])"
    ),
    "product_category": "nav.breadcrumb a, .breadcrumb a, [class*='breadcrumb'] a",
    "product_description": ".product-description, [class*='description'], .product-details",
    "product_sku": "[class*='sku'], [class*='reference'], .product-ref",
    "product_image": ".product-image img, .product__image img, [class*='product'] img[src]",
    "next_page": "a[rel='next'], .pagination a.next, [class*='pagination'] a:last-child",
}


def _throttle():
    delay = SCRAPE_SETTINGS["delay_between_requests"]
    time.sleep(random.uniform(delay * 0.8, delay * 1.2))


def _get_page(url, session):
    try:
        _throttle()
        response = session.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return BeautifulSoup(response.text, "lxml")
    except Exception:
        return None


def _extract_text(soup, selector):
    for sel in selector.split(", "):
        element = soup.select_one(sel.strip())
        if element:
            return element.get_text(separator=" ", strip=True)
    return ""


def _extract_price(soup, selector):
    raw = _extract_text(soup, selector)
    if not raw:
        return ""
    price = re.sub(r"[^\d.,٠-٩]", "", raw)
    arabic_nums = "٠١٢٣٤٥٦٧٨٩"
    for index, char in enumerate(arabic_nums):
        price = price.replace(char, str(index))
    return price


def _extract_category(soup, selector):
    for sel in selector.split(", "):
        items = soup.select(sel.strip())
        if len(items) >= 2:
            return items[-2].get_text(strip=True)
        if items:
            return items[-1].get_text(strip=True)
    return ""


def _extract_image_url(soup, selector, base_url):
    for sel in selector.split(", "):
        img = soup.select_one(sel.strip())
        if img:
            src = img.get("data-src") or img.get("data-original") or img.get("src", "")
            if src and not src.startswith("data:"):
                return urljoin(base_url, src)
    return ""


def _scrape_product(url, session, base_url):
    soup = _get_page(url, session)
    if not soup:
        return None
    return {
        "name": _extract_text(soup, SELECTORS["product_name"]),
        "price": _extract_price(soup, SELECTORS["product_price"]),
        "category": _extract_category(soup, SELECTORS["product_category"]),
        "description": _extract_text(soup, SELECTORS["product_description"])[:500],
        "sku": _extract_text(soup, SELECTORS["product_sku"]),
        "image_url": _extract_image_url(soup, SELECTORS["product_image"], base_url),
        "product_url": url,
    }


def _get_product_links(soup, base_url):
    links = set()
    for card in soup.select(SELECTORS["product_card"]):
        anchor = card.select_one(SELECTORS["product_link"])
        if anchor and anchor.get("href"):
            links.add(urljoin(base_url, anchor["href"]))
    return links


def _get_next_page(soup, base_url):
    for sel in SELECTORS["next_page"].split(", "):
        anchor = soup.select_one(sel.strip())
        if anchor and anchor.get("href") and anchor["href"] not in ["#", ""]:
            return urljoin(base_url, anchor["href"])
    return None


def scrape_html_category(
    url: str,
    session: requests.Session,
    max_pages: int,
    on_progress=None,
) -> list[dict]:
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    all_product_links = set()
    current_url = url
    page_num = 0

    while current_url and (max_pages == 0 or page_num < max_pages):
        page_num += 1
        if on_progress:
            on_progress("scrape_page", page_num, max_pages or 0, current_url)
        soup = _get_page(current_url, session)
        if not soup:
            break
        all_product_links.update(_get_product_links(soup, base_url))
        current_url = _get_next_page(soup, base_url)

    products = []
    total = len(all_product_links)
    for index, product_url in enumerate(sorted(all_product_links), start=1):
        if on_progress:
            on_progress("scrape_product", index, total, product_url[:60])
        data = _scrape_product(product_url, session, base_url)
        if data and data.get("name"):
            products.append(data)
    return products
