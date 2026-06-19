"""فصل السعة/الحجم/الوزن عن اسم المنتج."""

from __future__ import annotations

import re


def normalize_name(name: str) -> str:
    return (name or "").replace("'", "'").strip()

_SIZE_SEGMENT = re.compile(
    r"Pack of\s+\d+|"
    r"عبوة\s*(?:من\s+)?\d+|"
    r"\d+(?:[.,]\d+)?\s*(?:Liter|Liters|Litre|Litres|L|ml|milliliter|millilitre|مل|لتر|كيلو|كجم)\b|"
    r"\d+(?:[.,]\d+)?\s*(?:kg|kilo|kilogram|g|gram|grams|gr|غرام|جم)\b|"
    r"\d+\s*(?:Piece|Pieces|Pc|PCS|قطعة|قطع|حبة|حبات)\b|"
    r"بالقطعة",
    re.I,
)


def split_name_and_size(name: str) -> tuple[str, str]:
    """يفصل اسم المنتج عن السعة/الحجم/الوزن."""
    name = normalize_name(name)
    if not name:
        return "", ""

    parts: list[str] = []
    for match in _SIZE_SEGMENT.finditer(name):
        part = match.group(0).strip(" -–,")
        if part and part not in parts:
            parts.append(part)

    clean_name = _SIZE_SEGMENT.sub(" ", name)
    clean_name = re.sub(r"\s*,\s*", "، ", clean_name)
    clean_name = re.sub(r"\s+", " ", clean_name).strip(" -–,،")

    return clean_name, " - ".join(parts)


def strip_size_from_name(name: str) -> str:
    """اسم المنتج بدون السعة/الحجم/الوزن."""
    clean_name, _ = split_name_and_size(name)
    return clean_name
