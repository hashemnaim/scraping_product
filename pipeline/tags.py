"""توليد Tags للبحث: اسم المنتج + التصنيف بأشكال ومرادفات متعددة."""

from __future__ import annotations

import re

STOP_WORDS = frozenset(
    {
        "and",
        "the",
        "of",
        "for",
        "with",
        "من",
        "و",
        "في",
        "على",
        "the",
        "a",
        "an",
    }
)

UNIT_SUFFIX_PATTERNS = [
    re.compile(r"\s*[-–]\s*\d+\s*(Piece|Pieces|Pc|PCS|قطعة|قطع|حبة|حبات)\b", re.I),
    re.compile(r"\s*[-–]\s*\d+(?:[.,]\d+)?\s*(kg|kilo|g|gram|ml|كيلو|كجم|غرام|جم|مل)\b", re.I),
    re.compile(r"\s+\d+(?:[.,]\d+)?\s*(kg|kilo|g|gram|grams|gr|ml|كيلو|كجم|غرام|جم|مل)\b", re.I),
    re.compile(r"\s+\d+\s*(Piece|Pieces|Pc|PCS|قطعة|قطع|حبة|حبات)\b", re.I),
    re.compile(r"\s+بالقطعة\b"),
]

COMMON_SYNONYMS: dict[str, list[str]] = {
    "chips": ["chips", "chip", "crisps", "شيبس", "شيبسي", "بطاطس مقلية"],
    "chocolate": ["chocolate", "choco", "شوكولاتة", "شيكولاته", "شوكولاته"],
    "water": ["water", "مياه", "ماء"],
    "milk": ["milk", "لبن", "حليب"],
    "cheese": ["cheese", "جبن", "جبنة"],
    "juice": ["juice", "عصير", "عصائر"],
    "soap": ["soap", "صابون"],
    "shampoo": ["shampoo", "شامبو"],
    "detergent": ["detergent", "منظف", "غسيل"],
}


def normalize_name(name: str) -> str:
    return (name or "").replace("'", "'").strip()


def _with_al(word: str) -> str | None:
    word = word.strip()
    if len(word) < 2 or word.startswith("ال"):
        return None
    return f"ال{word}"


def _strip_unit_suffixes(name: str) -> str:
    cleaned = normalize_name(name)
    for pattern in UNIT_SUFFIX_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip(" -–")


def _english_variants(name: str) -> list[str]:
    variants: list[str] = []
    base = normalize_name(name)
    if not base:
        return variants

    lowered = base.lower()
    compact = re.sub(r"[^\w\s]", " ", base, flags=re.UNICODE)
    compact = re.sub(r"\s+", " ", compact).strip()
    compact_lower = compact.lower()

    for value in (base, lowered, compact, compact_lower):
        if value and value not in variants:
            variants.append(value)

    # hyphenated brand forms: lay's -> lays
    no_apostrophe = base.replace("'", "").replace("'", "")
    if no_apostrophe and no_apostrophe not in variants:
        variants.append(no_apostrophe)
        variants.append(no_apostrophe.lower())

    return variants


def _tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.split(r"[\s()\-–,/]+", text)
        if token and token.lower() not in STOP_WORDS and len(token) > 1 and not token.isdigit()
    ]


def _arabic_variants(text: str) -> list[str]:
    variants: list[str] = []
    normalized = normalize_name(text)
    if not normalized:
        return variants

    if normalized not in variants:
        variants.append(normalized)

    with_al = _with_al(normalized)
    if with_al and with_al not in variants:
        variants.append(with_al)

    for token in _tokenize(normalized):
        if token not in variants:
            variants.append(token)
        token_al = _with_al(token)
        if token_al and token_al not in variants:
            variants.append(token_al)

    parts = re.split(r"\s+و\s+|\s+", normalized)
    for part in parts:
        part = part.strip()
        if len(part) > 1 and part not in variants:
            variants.append(part)
        part_al = _with_al(part)
        if part_al and part_al not in variants:
            variants.append(part_al)

    return variants


def _phrase_combos(*parts: str) -> list[str]:
    combos: list[str] = []
    clean_parts = [normalize_name(part) for part in parts if normalize_name(part)]
    if not clean_parts:
        return combos

    full = " ".join(clean_parts)
    if full not in combos:
        combos.append(full)

    if len(clean_parts) >= 2:
        reversed_full = " ".join(reversed(clean_parts))
        if reversed_full not in combos:
            combos.append(reversed_full)

    return combos


def build_search_tags(
    product_name: str,
    category_name: str = "",
    subcategory_name: str = "",
    source_category: str = "",
    arabic_only: bool = False,
) -> str:
    """بناء كلمات مفتاحية للبحث من اسم المنتج والتصنيف."""
    tags: list[str] = []

    def add(*values: str):
        for value in values:
            if not value:
                continue
            text = str(value).strip()
            if not text:
                continue
            if arabic_only and not _is_arabic_tag(text):
                continue
            if text not in tags:
                tags.append(text)

    product_name = normalize_name(product_name)
    category_name = normalize_name(category_name)
    subcategory_name = normalize_name(subcategory_name)
    source_category = normalize_name(source_category)
    clean_product = _strip_unit_suffixes(product_name)

    add(product_name)
    if clean_product and clean_product != product_name:
        add(clean_product)

    if not arabic_only:
        add(*_english_variants(product_name))
        if clean_product:
            add(*_english_variants(clean_product))

    add(*_arabic_variants(clean_product or product_name))

    labels = [category_name, subcategory_name]
    if not arabic_only or _is_arabic_tag(source_category):
        labels.append(source_category)

    for label in labels:
        add(label)
        add(*_arabic_variants(label))

    add(*_phrase_combos(category_name, product_name))
    add(*_phrase_combos(subcategory_name, product_name))
    add(*_phrase_combos(category_name, clean_product))
    add(*_phrase_combos(subcategory_name, clean_product))
    add(*_phrase_combos(category_name, subcategory_name, product_name))

    tokens = _tokenize(clean_product or product_name)
    for index in range(len(tokens)):
        for length in range(2, min(4, len(tokens) - index + 1)):
            add(" ".join(tokens[index : index + length]))
    for token in tokens:
        add(token)

    if not arabic_only:
        lowered_tokens = [token.lower() for token in tokens]
        for key, synonyms in COMMON_SYNONYMS.items():
            if key in lowered_tokens or key in (clean_product or product_name).lower():
                add(key, *synonyms)
    else:
        lowered_tokens = [token.lower() for token in tokens]
        for key, synonyms in COMMON_SYNONYMS.items():
            if key in lowered_tokens or key in (clean_product or product_name).lower():
                add(*(syn for syn in synonyms if _is_arabic_tag(syn)))

    return ", ".join(tags)


def _is_arabic_tag(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text))
