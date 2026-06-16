"""قواعد ربط نص تصنيف الموقع المصدر بالتصنيف الفرعي في الكتالوج."""

from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.catalog import CategoryMappingRule


def _normalize_text(text: str) -> str:
    normalized = (text or "").strip().lower()
    for src, dst in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي")):
        normalized = normalized.replace(src, dst)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _rule_matches(source_norm: str, rule: CategoryMappingRule) -> bool:
    pattern_norm = _normalize_text(rule.pattern)
    if not pattern_norm or not source_norm:
        return False
    if rule.match_mode == "equals":
        return source_norm == pattern_norm
    return pattern_norm in source_norm


def resolve_subcategory(
    source_category_text: str,
    default_sub_category_id: int,
    rules: list[CategoryMappingRule],
) -> tuple[int, bool, bool]:
    """يرجع (sub_category_id, rule_applied, conflict)."""
    source_norm = _normalize_text(source_category_text)
    if not source_norm or not rules:
        return default_sub_category_id, False, False

    active_rules = [rule for rule in rules if rule.active]
    matches: list[CategoryMappingRule] = []
    for rule in active_rules:
        if _rule_matches(source_norm, rule):
            matches.append(rule)

    if not matches:
        return default_sub_category_id, False, False

    matches.sort(key=lambda rule: (rule.priority, len(rule.pattern)), reverse=True)
    best_priority = matches[0].priority
    top = [rule for rule in matches if rule.priority == best_priority]
    top.sort(key=lambda rule: len(rule.pattern), reverse=True)

    if len(top) > 1 and len({rule.sub_category_id for rule in top}) > 1:
        return default_sub_category_id, False, True

    chosen = top[0]
    if chosen.sub_category_id == default_sub_category_id:
        return default_sub_category_id, False, False
    return chosen.sub_category_id, True, False
