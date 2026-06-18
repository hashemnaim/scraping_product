"""تحويل أسماء المنتجات الإنجليزية إلى عربية للتصدير."""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

from pipeline.paths import catalog_dir

_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")

_PHRASE_REPLACEMENTS: list[tuple[str, str]] = [
    ("soft drink", "مشروب غازي"),
    ("energy drink", "مشروب طاقة"),
    ("sparkling drink", "مشروب غازي"),
    ("caffeine drink", "مشروب كافيين"),
    ("extra caffeine", "كافيين إضافي"),
    ("white peach", "خوخ أبيض"),
    ("lemon mint", "ليمون ونعناع"),
    ("fruit salad", "سلطة فواكه"),
    ("for juice", "للعصير"),
    ("pack of", "عبوة"),
    ("red bull", "ريد بول"),
    ("coca cola", "كوكا كولا"),
    ("coca-cola", "كوكا كولا"),
    ("seven up", "سفن أب"),
    ("kit kat", "كيت كات"),
    ("v super", "في سوبر"),
    ("big cola", "بيج كولا"),
    ("big lemon", "بيج ليمون"),
]

_WORD_REPLACEMENTS: dict[str, str] = {
    "cola": "كولا",
    "soda": "صودا",
    "drink": "مشروب",
    "drinks": "مشروبات",
    "water": "مياه",
    "juice": "عصير",
    "juices": "عصائر",
    "milk": "حليب",
    "cheese": "جبن",
    "chips": "شيبس",
    "chocolate": "شوكولاتة",
    "with": "بنكهة",
    "and": "و",
    "mint": "نعناع",
    "lemon": "ليمون",
    "peach": "خوخ",
    "extra": "إكسترا",
    "caffeine": "كافيين",
    "energy": "طاقة",
    "soft": "غازي",
    "sparkling": "غازي",
    "imported": "مستورد",
    "prepared": "مقطع",
    "fresh": "طازج",
    "organic": "عضوي",
    "natural": "طبيعي",
    "diet": "دايت",
    "light": "لايت",
    "zero": "زيرو",
    "big": "بيج",
    "super": "سوبر",
    "piece": "قطعة",
    "pieces": "قطع",
    "pack": "عبوة",
    "bottle": "زجاجة",
    "can": "علبة",
    "flavor": "نكهة",
    "flavored": "بنكهة",
    "flavour": "نكهة",
    "flavoured": "بنكهة",
}


def contains_arabic(text: str) -> bool:
    return bool(_ARABIC_RE.search(text or ""))


@lru_cache(maxsize=1)
def _brand_alias_map() -> dict[str, str]:
    brands_path = catalog_dir() / "brands.csv"
    aliases_path = catalog_dir() / "brand_aliases.csv"
    if not brands_path.exists() or not aliases_path.exists():
        return {}

    brand_names: dict[int, str] = {}
    with brands_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                brand_id = int(row.get("id") or 0)
            except ValueError:
                continue
            name = (row.get("name") or "").strip()
            if brand_id and name:
                brand_names[brand_id] = name

    mapping: dict[str, str] = {}
    with aliases_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                brand_id = int(row.get("brand_id") or 0)
            except ValueError:
                continue
            alias = (row.get("alias") or "").strip().lower()
            name = brand_names.get(brand_id, "")
            if alias and name:
                mapping[alias] = name
    return mapping


def _apply_regex_units(text: str) -> str:
    rules = [
        (re.compile(r"\bPack of\s+(\d+)\b", re.I), r"عبوة \1"),
        (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*ml\b", re.I), r"\1 مل"),
        (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(?:Liter|Liters|Litre|Litres|L)\b", re.I), r"\1 لتر"),
        (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*kg\b", re.I), r"\1 كجم"),
        (re.compile(r"\b(\d+(?:[.,]\d+)?)\s*g\b", re.I), r"\1 جم"),
        (re.compile(r"\b(\d+)\s*(?:Piece|Pieces|Pc|PCS)\b", re.I), r"\1 قطعة"),
    ]
    result = text
    for pattern, replacement in rules:
        result = pattern.sub(replacement, result)
    return result


def _apply_phrases(text: str) -> str:
    result = text
    for source, target in sorted(_PHRASE_REPLACEMENTS, key=lambda item: -len(item[0])):
        result = re.sub(re.escape(source), target, result, flags=re.I)
    return result


def _apply_brand_aliases(text: str) -> str:
    lowered = text.lower()
    for alias, brand_name in sorted(_brand_alias_map().items(), key=lambda item: -len(item[0])):
        pattern = re.compile(rf"\b{re.escape(alias)}\b", re.I)
        if pattern.search(lowered):
            text = pattern.sub(brand_name, text)
            lowered = text.lower()
    return text


def _apply_words(text: str) -> str:
    def replace_word(match: re.Match[str]) -> str:
        word = match.group(0)
        mapped = _WORD_REPLACEMENTS.get(word.lower())
        return mapped if mapped else word

    return re.sub(r"[A-Za-z]+(?:'[A-Za-z]+)?", replace_word, text)


def _cleanup(text: str) -> str:
    text = text.replace("'", "'")
    text = re.sub(r"\s*,\s*", "، ", text)
    text = re.sub(r"\s*-\s*", " - ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -–،")


def localize_product_name(name: str) -> str:
    """حوّل اسم المنتج إلى عربي؛ إن كان عربياً يُعاد كما هو."""
    name = (name or "").replace("'", "'").strip()
    if not name:
        return ""
    if contains_arabic(name):
        return _cleanup(name)

    text = _apply_regex_units(name)
    text = _apply_phrases(text)
    text = _apply_brand_aliases(text)
    text = _apply_words(text)
    return _cleanup(text)
