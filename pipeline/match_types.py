"""أنواع نتائج المطابقة والإثراء — مشتركة بين الوحدات والعلامات والمراجعة."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class FieldSource(str, Enum):
    USER_SELECTION = "user_selection"
    SCRAPED = "scraped"
    INFERRED_NAME = "inferred_name"
    CATALOG_DEFAULT = "catalog_default"
    INFERRED_RULE = "inferred_rule"


class WarningFlag(str, Enum):
    DEFAULT_UNIT = "default_unit"
    AMBIGUOUS_UNIT = "ambiguous_unit"
    MISSING_BRAND = "missing_brand"
    MISSING_PRICE = "missing_price"
    FAILED_IMAGE = "failed_image"
    CATEGORY_RULE_APPLIED = "category_rule_applied"
    CATEGORY_RULE_CONFLICT = "category_rule_conflict"


@dataclass(frozen=True)
class UnitMatchResult:
    unit_id: int | None
    quantity_unit: str | None
    confidence: str  # high | medium | low
    reason: str


@dataclass(frozen=True)
class BrandMatchResult:
    brand_id: int | None
    confidence: str  # high | medium | low | none
    reason: str


@dataclass
class FieldEnrichment:
    product_id: int
    product_name: str
    unit: UnitMatchResult
    brand: BrandMatchResult
    warnings: list[str] = field(default_factory=list)
    source_category: str = ""
    resolved_sub_category_id: int | None = None
