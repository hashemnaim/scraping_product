"""سحب سعودي سوبرماركت عبر GraphQL."""

from __future__ import annotations

import random
import re
import time
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from pipeline.constants import HEADERS, SCRAPE_SETTINGS

CATEGORY_PRODUCTS_QUERY = """
query CategoryProducts($urlPath: String!, $pageSize: Int!, $currentPage: Int!) {
  categoryList(filters: { url_path: { eq: $urlPath } }) {
    name
    url_path
    products(pageSize: $pageSize, currentPage: $currentPage) {
      items {
        name
        sku
        url_key
        price_range {
          minimum_price {
            final_price {
              value
              currency
            }
          }
        }
        image {
          url
        }
      }
      page_info {
        current_page
        total_pages
      }
      total_count
    }
  }
}
"""

PRODUCT_DETAIL_QUERY = """
query ProductDetail($sku: String!) {
  products(filter: { sku: { eq: $sku } }) {
    items {
      description {
        html
      }
    }
  }
}
"""


def _throttle():
    delay = SCRAPE_SETTINGS["delay_between_requests"]
    time.sleep(random.uniform(delay * 0.8, delay * 1.2))


def _graphql_request(session, query, variables):
    _throttle()
    response = session.post(
        SCRAPE_SETTINGS["graphql_endpoint"],
        json={"query": query, "variables": variables},
        headers={**HEADERS, "Content-Type": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "GraphQL error"))
    return payload.get("data", {})


def parse_seoudi_url(url: str):
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]
    locale = "ar"
    category_parts = path_parts
    if path_parts and path_parts[0] in {"ar", "en"}:
        locale = path_parts[0]
        category_parts = path_parts[1:]
    if not category_parts:
        raise ValueError("تعذّر استخراج مسار الفئة من الرابط")
    category_path = "/".join(category_parts)
    query = parse_qs(parsed.query)
    start_page = int(query.get("page", ["1"])[0])
    return locale, category_path, start_page


def _upgrade_image_url(url: str) -> str:
    if not url or not SCRAPE_SETTINGS["download_full_image"]:
        return url
    return re.sub(r"/media/catalog/product/cache/[^/]+/", "/media/catalog/product/", url)


def _fetch_description(session, sku: str) -> str:
    if not SCRAPE_SETTINGS["fetch_descriptions"] or not sku:
        return ""
    try:
        data = _graphql_request(session, PRODUCT_DETAIL_QUERY, {"sku": sku})
        items = data.get("products", {}).get("items", [])
        if not items:
            return ""
        html = items[0].get("description", {}).get("html", "") or ""
        if not html:
            return ""
        return BeautifulSoup(html, "lxml").get_text(separator=" ", strip=True)[:500]
    except Exception:
        return ""


def scrape_seoudi_category(
    url: str,
    session: requests.Session,
    max_pages: int,
    on_progress=None,
) -> list[dict]:
    locale, category_path, start_page = parse_seoudi_url(url)
    base_url = f"https://seoudisupermarket.com/{locale}"
    products = []
    pages_fetched = 0
    current_page = start_page
    total_pages = None

    while max_pages == 0 or pages_fetched < max_pages:
        pages_fetched += 1
        if on_progress:
            on_progress("scrape_page", current_page, total_pages or 0, f"صفحة {current_page}")

        data = _graphql_request(
            session,
            CATEGORY_PRODUCTS_QUERY,
            {
                "urlPath": category_path,
                "pageSize": SCRAPE_SETTINGS["graphql_page_size"],
                "currentPage": current_page,
            },
        )
        categories = data.get("categoryList") or []
        if not categories:
            break

        category = categories[0]
        category_name = category.get("name", "")
        product_block = category.get("products") or {}
        items = product_block.get("items") or []
        page_info = product_block.get("page_info") or {}
        total_pages = page_info.get("total_pages", total_pages)

        if not items:
            break

        for item in items:
            price_info = item.get("price_range", {}).get("minimum_price", {}).get("final_price", {})
            price_value = price_info.get("value", "")
            sku = item.get("sku", "")
            url_key = item.get("url_key", "")
            products.append(
                {
                    "name": item.get("name", ""),
                    "price": str(price_value) if price_value != "" else "",
                    "category": category_name,
                    "description": _fetch_description(session, sku),
                    "sku": sku,
                    "image_url": _upgrade_image_url((item.get("image") or {}).get("url", "")),
                    "product_url": f"{base_url}/{url_key}" if url_key else "",
                }
            )

        if total_pages and current_page >= total_pages:
            break
        current_page += 1

    return products
