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

CATEGORY_RESOLVE_QUERY = """
query ResolveCategory($urlPath: String!, $urlKey: String!) {
  byPath: categoryList(filters: { url_path: { eq: $urlPath } }) {
    url_path
    products(pageSize: 1, currentPage: 1) {
      total_count
    }
  }
  byKey: categoryList(filters: { url_key: { eq: $urlKey } }) {
    name
    url_path
    url_key
    products(pageSize: 1, currentPage: 1) {
      total_count
    }
  }
}
"""


def _throttle():
    delay = SCRAPE_SETTINGS["delay_between_requests"]
    time.sleep(random.uniform(delay * 0.8, delay * 1.2))


def _graphql_headers(locale: str = "ar") -> dict:
    headers = {**HEADERS, "Content-Type": "application/json"}
    if locale == "ar":
        headers["Store"] = "ar_EG"
    return headers


def _graphql_request(session, query, variables, locale: str = "ar"):
    _throttle()
    response = session.post(
        SCRAPE_SETTINGS["graphql_endpoint"],
        json={"query": query, "variables": variables},
        headers=_graphql_headers(locale),
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


def _pick_category_by_url_key(categories: list[dict], category_path: str) -> dict | None:
    if not categories:
        return None
    if len(categories) == 1:
        return categories[0]

    parent_prefix = "/".join(category_path.split("/")[:-1])
    parent_segment = parent_prefix.split("/")[-1] if parent_prefix else ""

    def score(category: dict) -> tuple[int, int]:
        url_path = category.get("url_path", "")
        total_count = (category.get("products") or {}).get("total_count") or 0
        path_match = 0
        if parent_prefix and url_path.startswith(f"{parent_prefix}/"):
            path_match = 3
        elif parent_segment and url_path.split("/")[-2:][0] == parent_segment:
            path_match = 2
        elif parent_segment and parent_segment in url_path.split("/"):
            path_match = 1
        return path_match, total_count

    return max(categories, key=score)


def resolve_graphql_category_path(
    session: requests.Session, category_path: str, locale: str = "ar"
) -> str:
    """حل مسار الفئة من رابط الموقع إلى url_path الفعلي في GraphQL."""
    url_key = category_path.rsplit("/", 1)[-1]
    data = _graphql_request(
        session,
        CATEGORY_RESOLVE_QUERY,
        {"urlPath": category_path, "urlKey": url_key},
        locale=locale,
    )
    by_path = data.get("byPath") or []
    if by_path and (by_path[0].get("products") or {}).get("total_count", 0) > 0:
        return by_path[0]["url_path"]

    by_key = data.get("byKey") or []
    picked = _pick_category_by_url_key(by_key, category_path)
    if picked and picked.get("url_path"):
        return picked["url_path"]

    if by_path:
        return by_path[0]["url_path"]
    return category_path


def _upgrade_image_url(url: str) -> str:
    if not url or not SCRAPE_SETTINGS["download_full_image"]:
        return url
    return re.sub(r"/media/catalog/product/cache/[^/]+/", "/media/catalog/product/", url)


def _fetch_description(session, sku: str, locale: str = "ar") -> str:
    if not SCRAPE_SETTINGS["fetch_descriptions"] or not sku:
        return ""
    try:
        data = _graphql_request(session, PRODUCT_DETAIL_QUERY, {"sku": sku}, locale=locale)
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
    start_page: int | None = None,
) -> list[dict]:
    locale, category_path, url_start_page = parse_seoudi_url(url)
    graphql_category_path = resolve_graphql_category_path(session, category_path, locale)
    base_url = f"https://seoudisupermarket.com/{locale}"
    products = []
    pages_fetched = 0
    current_page = start_page if start_page is not None else url_start_page
    total_pages = None

    while max_pages == 0 or pages_fetched < max_pages:
        pages_fetched += 1
        if on_progress:
            on_progress("scrape_page", current_page, total_pages or 0, f"صفحة {current_page}")

        data = _graphql_request(
            session,
            CATEGORY_PRODUCTS_QUERY,
            {
                "urlPath": graphql_category_path,
                "pageSize": SCRAPE_SETTINGS["graphql_page_size"],
                "currentPage": current_page,
            },
            locale=locale,
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
                    "description": _fetch_description(session, sku, locale),
                    "sku": sku,
                    "image_url": _upgrade_image_url((item.get("image") or {}).get("url", "")),
                    "product_url": f"{base_url}/{url_key}" if url_key else "",
                }
            )

        if total_pages and current_page >= total_pages:
            break
        current_page += 1

    return products
