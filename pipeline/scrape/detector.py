"""كشف مصدر السحب وتوجيه الطلب."""

from __future__ import annotations

from urllib.parse import urlparse

import requests

from pipeline.scrape import html_scraper, instashop, seoudi_graphql


def is_seoudi_domain(url: str) -> bool:
    return "seoudisupermarket.com" in urlparse(url).netloc


def is_instashop_domain(url: str) -> bool:
    return "instashop.com" in urlparse(url).netloc


def detect_mode(url: str, mode: str = "auto") -> str:
    if mode != "auto":
        return mode
    if is_seoudi_domain(url):
        return "graphql"
    if is_instashop_domain(url):
        return "instashop"
    return "html"


def scrape_category(
    url: str,
    session: requests.Session,
    max_pages: int,
    mode: str = "auto",
    on_progress=None,
    start_page: int = 1,
) -> list[dict]:
    resolved = detect_mode(url, mode)
    if resolved == "graphql":
        return seoudi_graphql.scrape_seoudi_category(
            url, session, max_pages, on_progress, start_page=start_page
        )
    if resolved == "instashop":
        return instashop.scrape_instashop_category(url, on_progress)
    return html_scraper.scrape_html_category(url, session, max_pages, on_progress)
