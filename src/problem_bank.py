"""Premium problem-bank constants and query helpers."""

from __future__ import annotations

from typing import Iterable, Optional


PREMIUM_DATASET_TIER = "premium"
LEGACY_DATASET_TIER = "legacy"

RECOMMENDATION_EDGE_TYPES = {
    "prerequisite",
    "alternative",
    "follow_up",
    "review",
    "recovery",
    "related",
}

RAG_CHUNK_TYPES = {
    "statement",
    "editorial",
    "hints",
    "common_mistakes",
    "learning_objectives",
}


def active_problem_clause(alias: Optional[str] = None) -> str:
    prefix = f"{alias}." if alias else ""
    return f"{prefix}dataset_tier = '{PREMIUM_DATASET_TIER}' AND {prefix}is_active = 1"


def in_clause(values: Iterable[str]) -> str:
    items = list(values)
    if not items:
        raise ValueError("in_clause requires at least one value")
    return ",".join(["?"] * len(items))
