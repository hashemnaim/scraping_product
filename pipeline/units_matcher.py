"""استخراج UnitId و QuantityUnit من اسم المنتج — القطعة أولاً ثم الوزن/الحجم."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pipeline.match_types import UnitMatchResult

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

_WEIGHT_CATEGORY_KEYWORDS = (
    "خضروات",
    "خضار",
    "فواكه",
    "فاكهة",
    "جبن",
    "جبنة",
    "أجبان",
    "اجبان",
    "لبنة",
)


def _normalize_quantity(raw: str) -> int | float:
    quantity = raw.replace(",", ".")
    if "." in quantity:
        value = float(quantity)
        return int(value) if value.is_integer() else value
    return int(quantity)


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


def _match_piece(name: str, units: list[Unit]) -> tuple[int | None, int | float | None]:
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
        return piece_unit.unit_id, 1
    return None, None


def _match_by_patterns(
    name: str,
    units: list[Unit],
    patterns: list[tuple[re.Pattern[str], frozenset[str]]],
) -> tuple[int | None, int | float | None]:
    for pattern, markers in patterns:
        match = pattern.search(name)
        if not match:
            continue
        unit = _find_unit_by_markers(units, markers)
        if unit is None:
            continue
        return unit.unit_id, _normalize_quantity(match.group(1))
    return None, None


def _normalize_category_text(text: str) -> str:
    normalized = (text or "").strip()
    for src, dst in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه")):
        normalized = normalized.replace(src, dst)
    return normalized.lower()


def category_allows_weight_units(category_name: str, subcategory_name: str) -> bool:
    """تصنيفات تحتفظ بوحدات الوزن/الحجم من اسم المنتج (خضروات، فواكه، أجبان)."""
    haystack = _normalize_category_text(f"{category_name} {subcategory_name}")
    return any(keyword in haystack for keyword in _WEIGHT_CATEGORY_KEYWORDS)


def _is_piece_unit_id(unit_id: int | None, units: list[Unit]) -> bool:
    if unit_id is None:
        return False
    piece_unit = _find_piece_unit(units)
    return piece_unit is not None and piece_unit.unit_id == unit_id


def _has_weight_marker(name: str) -> bool:
    return any(pattern.search(name) for pattern, _ in WEIGHT_PATTERNS)


def _has_volume_marker(name: str) -> bool:
    return any(pattern.search(name) for pattern, _ in VOLUME_PATTERNS)


def _piece_one(units: list[Unit]) -> tuple[int | None, int | float | None]:
    piece_unit = _find_piece_unit(units)
    if piece_unit is None:
        return None, None
    return piece_unit.unit_id, 1


def _is_gram_or_kilo_unit(unit_id: int | None, units: list[Unit]) -> bool:
    if unit_id is None:
        return False
    weight_markers = frozenset({"كيلو", "غرام", "kg", "kilo", "kilogram", "كجم", "g", "gram", "grams", "gr", "جم"})
    for unit in units:
        if unit.unit_id != unit_id:
            continue
        keywords = _unit_keywords(unit)
        return bool(keywords & weight_markers)
    return False


def finalize_unit_for_export(
    unit_id: int | None,
    quantity_unit: int | float | None,
    units: list[Unit],
) -> tuple[int | None, int | float | None]:
    """بعد المطابقة: غير غرام/كيلو → قطعة، ولا تُترك الوحدة فارغة."""
    if unit_id is not None and _is_gram_or_kilo_unit(unit_id, units):
        return unit_id, quantity_unit if quantity_unit is not None else 1

    piece_unit = _find_piece_unit(units)
    if piece_unit is None:
        return unit_id, quantity_unit

    if _is_piece_unit_id(unit_id, units):
        return unit_id, quantity_unit if quantity_unit is not None else 1

    return piece_unit.unit_id, 1


def _count_unit_pattern_hits(name: str) -> int:
    normalized = (name or "").replace("'", "'").strip()
    hits = 0
    if any(p.search(normalized) for p in PIECE_PATTERNS):
        hits += 1
    if any(p.search(normalized) for p, _ in WEIGHT_PATTERNS):
        hits += 1
    if any(p.search(normalized) for p, _ in VOLUME_PATTERNS):
        hits += 1
    if any(p.search(normalized) for p, _ in OTHER_PATTERNS):
        hits += 1
    return hits


def _infer_unit_meta(
    name: str,
    raw_unit_id: int | None,
    raw_qty: int | float | None,
    final_unit_id: int | None,
    final_qty: int | float | None,
    units: list[Unit],
    *,
    category_name: str,
    subcategory_name: str,
    ambiguous: bool,
) -> UnitMatchResult:
    if ambiguous:
        return UnitMatchResult(final_unit_id, final_qty, "low", "ambiguous_unit")

    if not name or not units:
        return UnitMatchResult(final_unit_id, final_qty, "low", "no_marker")

    allows_weight = category_allows_weight_units(category_name, subcategory_name)
    normalized = (name or "").replace("'", "'").strip()

    if raw_unit_id is not None:
        piece_hit = _match_piece(normalized, units)[0] is not None
        weight_hit = _has_weight_marker(normalized)
        volume_hit = _has_volume_marker(normalized)

        if piece_hit and not weight_hit and not volume_hit:
            return UnitMatchResult(final_unit_id, final_qty, "medium", "pattern_piece")

        if allows_weight and (weight_hit or volume_hit):
            if weight_hit:
                return UnitMatchResult(final_unit_id, final_qty, "high", "pattern_weight")
            return UnitMatchResult(final_unit_id, final_qty, "high", "pattern_volume")

        if not allows_weight and (weight_hit or volume_hit) and _is_piece_unit_id(final_unit_id, units):
            return UnitMatchResult(final_unit_id, final_qty, "low", "category_forced_piece")

        if raw_unit_id == final_unit_id:
            return UnitMatchResult(final_unit_id, final_qty, "high", "pattern_other")

    if _is_piece_unit_id(final_unit_id, units) and (final_qty or 1) == 1:
        return UnitMatchResult(final_unit_id, final_qty, "low", "default_piece")

    return UnitMatchResult(final_unit_id, final_qty, "medium", "pattern_matched")


def match_unit_with_meta(
    name: str,
    units: list[Unit],
    *,
    category_name: str = "",
    subcategory_name: str = "",
) -> UnitMatchResult:
    ambiguous = _count_unit_pattern_hits(name) > 1
    raw_unit_id, raw_qty = match_unit(name, units)
    unit_id, quantity_unit = match_unit_for_category(
        name,
        units,
        category_name=category_name,
        subcategory_name=subcategory_name,
    )
    final_id, final_qty = finalize_unit_for_export(unit_id, quantity_unit, units)
    return _infer_unit_meta(
        name,
        raw_unit_id,
        raw_qty,
        final_id,
        final_qty,
        units,
        category_name=category_name,
        subcategory_name=subcategory_name,
        ambiguous=ambiguous,
    )


def match_unit_for_category(
    name: str,
    units: list[Unit],
    *,
    category_name: str = "",
    subcategory_name: str = "",
) -> tuple[int | None, int | float | None]:
    """مطابقة وحدة مع قواعد التصنيف: خارج الاستثناءات → g/kg/ml تصبح قطعة + 1."""
    unit_id, quantity_unit = match_unit(name, units)
    if not name or not units:
        return unit_id, quantity_unit

    if category_allows_weight_units(category_name, subcategory_name):
        return unit_id, quantity_unit

    if _is_piece_unit_id(unit_id, units):
        return unit_id, quantity_unit

    normalized = (name or "").replace("'", "'").strip()
    if _has_weight_marker(normalized) or _has_volume_marker(normalized):
        return _piece_one(units)

    return unit_id, quantity_unit


def match_unit(name: str, units: list[Unit]) -> tuple[int | None, int | float | None]:
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
