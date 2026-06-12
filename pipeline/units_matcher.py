"""استخراج UnitId و QuantityUnit من اسم المنتج — القطعة أولاً ثم الوزن/الحجم."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipeline.catalog import Unit

EXTRA_ALIASES: dict[str, list[str]] = {
    "قطعه": ["piece", "pieces", "pc", "pcs", "قطعة", "قطع", "حبة", "حبات", "بالقطعة"],
    "كيلو": ["kg", "kilo", "kilogram", "كجم", "كيلو"],
    "غرام": ["g", "gram", "grams", "gr", "جم", "غرام"],
    "فرط": ["فرط", "bunch"],
    "حزمة": ["حزمة", "pack", "bundle"],
    "ml": ["ml", "مل", "milliliter", "millilitre"],
}

PIECE_PATTERNS = [
    re.compile(r"(\d+)\s*(Piece|Pieces|Pc|PCS)\b", re.I),
    re.compile(r"(\d+)\s*(قطعة|قطع|حبة|حبات)\b"),
    re.compile(r"بالقطعة"),
]

WEIGHT_PATTERNS: list[tuple[re.Pattern[str], frozenset[str]]] = [
    (
        re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|kilo|kilogram|كيلو|كجم)\b", re.I),
        frozenset({"kg", "kilo", "kilogram", "كيلو", "كجم", "كيلو"}),
    ),
    (
        re.compile(r"(\d+(?:[.,]\d+)?)\s*(g|gram|grams|gr|غرام|جم)\b", re.I),
        frozenset({"g", "gram", "grams", "gr", "غرام", "جم", "غرام"}),
    ),
]

VOLUME_PATTERNS: list[tuple[re.Pattern[str], frozenset[str]]] = [
    (
        re.compile(r"(\d+(?:[.,]\d+)?)\s*(ml|مل|milliliter|millilitre)\b", re.I),
        frozenset({"ml", "مل", "milliliter", "millilitre"}),
    ),
]

OTHER_PATTERNS: list[tuple[re.Pattern[str], frozenset[str]]] = [
    (
        re.compile(r"(\d+)\s*(حزمة|pack|bundle)\b", re.I),
        frozenset({"حزمة", "pack", "bundle"}),
    ),
    (
        re.compile(r"(\d+)\s*(فرط|bunch)\b", re.I),
        frozenset({"فرط", "bunch"}),
    ),
]

PIECE_MARKERS = frozenset(
    {"قطعه", "قطعة", "قطع", "piece", "pieces", "pc", "pcs", "حبة", "حبات", "بالقطعة"}
)


def _normalize_quantity(raw: str) -> str:
    quantity = raw.replace(",", ".")
    if quantity.endswith(".0"):
        quantity = quantity[:-2]
    return quantity


def _unit_keywords(unit: Unit) -> set[str]:
    keywords = {unit.name_ar.strip().lower()}
    for alias in unit.aliases:
        token = alias.strip().lower()
        if token:
            keywords.add(token)
    for extra in EXTRA_ALIASES.get(unit.name_ar.strip(), []):
        keywords.add(extra.lower())
    return keywords


def _find_unit_by_markers(units: list[Unit], markers: frozenset[str]) -> Unit | None:
    for unit in units:
        if _unit_keywords(unit) & markers:
            return unit
    return None


def _find_piece_unit(units: list[Unit]) -> Unit | None:
    for unit in units:
        keywords = _unit_keywords(unit)
        if keywords & PIECE_MARKERS:
            return unit
        if any("قطع" in keyword for keyword in keywords):
            return unit
    return None


def _match_piece(name: str, units: list[Unit]) -> tuple[int | None, str | None]:
    piece_unit = _find_piece_unit(units)
    if piece_unit is None:
        return None, None

    for pattern in PIECE_PATTERNS:
        match = pattern.search(name)
        if not match:
            continue
        groups = match.groups()
        if groups:
            return piece_unit.unit_id, _normalize_quantity(groups[0])
        return piece_unit.unit_id, "1"
    return None, None


def _match_by_patterns(
    name: str,
    units: list[Unit],
    patterns: list[tuple[re.Pattern[str], frozenset[str]]],
) -> tuple[int | None, str | None]:
    for pattern, markers in patterns:
        match = pattern.search(name)
        if not match:
            continue
        unit = _find_unit_by_markers(units, markers)
        if unit is None:
            continue
        return unit.unit_id, _normalize_quantity(match.group(1))
    return None, None


def match_unit(name: str, units: list[Unit]) -> tuple[int | None, str | None]:
    """يرجع (unit_id, quantity_unit) من اسم المنتج."""
    if not name or not units:
        return None, None

    normalized = (name or "").replace("'", "'").strip()

    piece = _match_piece(normalized, units)
    if piece[0] is not None:
        return piece

    weight = _match_by_patterns(normalized, units, WEIGHT_PATTERNS)
    if weight[0] is not None:
        return weight

    volume = _match_by_patterns(normalized, units, VOLUME_PATTERNS)
    if volume[0] is not None:
        return volume

    other = _match_by_patterns(normalized, units, OTHER_PATTERNS)
    if other[0] is not None:
        return other

    return None, None
