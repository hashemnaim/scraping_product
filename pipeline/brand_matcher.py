"""مطابقة BrandId من اسم المنتج باستخدام catalog/brands.csv."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

from pipeline.paths import catalog_dir
from pipeline.match_types import BrandMatchResult

BRANDS_CSV = catalog_dir() / "brands.csv"
BRAND_ALIASES_CSV = catalog_dir() / "brand_aliases.csv"

_LATIN_RE = re.compile(r"[A-Za-z]{3,}")
_ARABIC_RE = re.compile(r"[\u0600-\u06FF]{2,}")


@dataclass(frozen=True)
class Brand:
    brand_id: int
    name: str
    slug: str
    module_id: int
    search_terms: tuple[str, ...]


def _normalize_text(text: str) -> str:
    normalized = (text or "").strip().lower()
    normalized = normalized.replace("'", "'").replace("’", "'")
    for src, dst in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي")):
        normalized = normalized.replace(src, dst)
    normalized = re.sub(r"[^\w\s\u0600-\u06FF'-]", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _slug_terms(slug: str) -> list[str]:
    if not slug:
        return []
    spaced = slug.replace("-", " ").replace("_", " ").strip()
    return [spaced] if spaced else []


def _brand_search_terms(name: str, slug: str) -> tuple[str, ...]:
    terms: list[str] = []
    seen: set[str] = set()
    candidates = [name, *_slug_terms(slug)]
    first_word = (name or "").split()[0] if name else ""
    if len(first_word) >= 3:
        candidates.append(first_word)
    for raw in candidates:
        norm = _normalize_text(raw)
        if len(norm) < 2 or norm in seen:
            continue
        seen.add(norm)
        terms.append(norm)
    return tuple(terms)


@lru_cache(maxsize=8)
def _load_alias_map(module_id: int | None) -> dict[str, int]:
    if not BRAND_ALIASES_CSV.is_file():
        return {}
    alias_map: dict[str, int] = {}
    with BRAND_ALIASES_CSV.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                brand_id = int(row.get("brand_id") or 0)
                row_module = int(row.get("module_id") or 0)
            except (TypeError, ValueError):
                continue
            if module_id is not None and row_module != module_id:
                continue
            alias = _normalize_text(row.get("alias") or "")
            if brand_id and len(alias) >= 2:
                alias_map[alias] = brand_id
    return alias_map


@lru_cache(maxsize=8)
def load_brands(module_id: int | None = None) -> tuple[Brand, ...]:
    if not BRANDS_CSV.is_file():
        return ()

    brands: list[Brand] = []
    with BRANDS_CSV.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                brand_module = int(row.get("module_id") or 0)
                brand_id = int(row.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if module_id is not None and brand_module != module_id:
                continue
            if int(row.get("status") or 1) != 1:
                continue
            name = (row.get("name") or "").strip()
            slug = (row.get("slug") or "").strip()
            if not name or not brand_id:
                continue
            brands.append(
                Brand(
                    brand_id=brand_id,
                    name=name,
                    slug=slug,
                    module_id=brand_module,
                    search_terms=_brand_search_terms(name, slug),
                )
            )
    brands.sort(key=lambda item: max(len(t) for t in item.search_terms), reverse=True)
    return tuple(brands)


def _tokenize(text: str) -> list[str]:
    return [token for token in _normalize_text(text).split() if len(token) >= 2]


def _alias_match(product_norm: str, module_id: int) -> int | None:
    alias_map = _load_alias_map(module_id)
    if not alias_map:
        return None
    for alias, brand_id in sorted(alias_map.items(), key=lambda item: len(item[0]), reverse=True):
        if alias in product_norm:
            return brand_id
    return None


def _substring_match(product_norm: str, brands: tuple[Brand, ...]) -> int | None:
    for brand in brands:
        for term in brand.search_terms:
            if len(term) < 4 and " " not in term:
                continue
            if term in product_norm:
                return brand.brand_id
    return None


def _word_match(product_norm: str, brands: tuple[Brand, ...]) -> int | None:
    product_words = set(_tokenize(product_norm))
    if not product_words:
        return None
    for brand in brands:
        for term in brand.search_terms:
            brand_words = _tokenize(term)
            if len(brand_words) >= 2 and all(word in product_words for word in brand_words):
                return brand.brand_id
    return None


def _latin_slug_match(product_name: str, brands: tuple[Brand, ...]) -> int | None:
    latin_chunks = [m.group(0).lower() for m in _LATIN_RE.finditer(product_name or "")]
    if not latin_chunks:
        return None
    haystack = " ".join(latin_chunks)
    for brand in brands:
        for term in brand.search_terms:
            if not re.search(r"[a-z]", term):
                continue
            if term in haystack:
                return brand.brand_id
            for slug_term in _slug_terms(brand.slug):
                slug_norm = _normalize_text(slug_term)
                if len(slug_norm) >= 3 and slug_norm in haystack:
                    return brand.brand_id
    return None


def _fuzzy_match(product_name: str, brands: tuple[Brand, ...]) -> int | None:
    product_norm = _normalize_text(product_name)
    candidates = _tokenize(product_norm)
    latin = [m.group(0).lower() for m in _LATIN_RE.finditer(product_name or "")]
    candidates.extend(latin)

    best_id: int | None = None
    best_score = 0.0
    for brand in brands:
        for term in brand.search_terms:
            if len(term) < 4:
                continue
            for candidate in candidates:
                if len(candidate) < 4:
                    continue
                score = SequenceMatcher(None, term, candidate).ratio()
                if score > best_score and score >= 0.88:
                    best_score = score
                    best_id = brand.brand_id
    return best_id


def match_brand_with_meta(product_name: str, module_id: int) -> BrandMatchResult:
    """يرجع BrandId مع مستوى الثقة والسبب."""
    if not product_name:
        return BrandMatchResult(None, "none", "empty_name")
    brands = load_brands(module_id)
    if not brands:
        return BrandMatchResult(None, "none", "no_catalog")

    product_norm = _normalize_text(product_name)
    brand_id = _alias_match(product_norm, module_id)
    if brand_id is not None:
        return BrandMatchResult(brand_id, "high", "alias")

    brand_id = _substring_match(product_norm, brands)
    if brand_id is not None:
        return BrandMatchResult(brand_id, "high", "substring")

    brand_id = _word_match(product_norm, brands)
    if brand_id is not None:
        return BrandMatchResult(brand_id, "high", "word")

    brand_id = _latin_slug_match(product_name, brands)
    if brand_id is not None:
        return BrandMatchResult(brand_id, "medium", "latin_slug")

    brand_id = _fuzzy_match(product_name, brands)
    if brand_id is not None:
        return BrandMatchResult(brand_id, "medium", "fuzzy")

    return BrandMatchResult(None, "none", "no_match")


def match_brand(product_name: str, module_id: int) -> int | None:
    """يرجع BrandId أو None إن لم يُعثر على تطابق."""
    return match_brand_with_meta(product_name, module_id).brand_id
