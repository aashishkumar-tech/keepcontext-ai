"""Metric helpers for quality evaluation."""

from __future__ import annotations

import re

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
}


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Compute precision@k for a retrieval result."""
    if k <= 0:
        return 0.0

    window = retrieved_ids[:k]
    if not window:
        return 0.0

    hits = sum(1 for item_id in window if item_id in relevant_ids)
    return hits / k


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Compute recall@k for a retrieval result."""
    if not relevant_ids:
        return 1.0

    window = retrieved_ids[:k]
    hits = sum(1 for item_id in window if item_id in relevant_ids)
    return hits / len(relevant_ids)


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """Compute reciprocal rank for a retrieval result."""
    for index, item_id in enumerate(retrieved_ids, start=1):
        if item_id in relevant_ids:
            return 1.0 / index
    return 0.0


def groundedness_score(response: str | None, evidence_text: str) -> float:
    """Estimate groundedness as lexical overlap against provided evidence."""
    if not response:
        return 0.0

    response_tokens = _normalize_tokens(response)
    if not response_tokens:
        return 0.0

    evidence_tokens = set(_normalize_tokens(evidence_text))
    if not evidence_tokens:
        return 0.0

    overlap_count = sum(1 for token in response_tokens if token in evidence_tokens)
    return overlap_count / len(response_tokens)


def _normalize_tokens(text: str) -> list[str]:
    """Tokenize and normalize text while dropping common stopwords."""
    tokens = [token.lower() for token in _TOKEN_PATTERN.findall(text)]
    return [token for token in tokens if token not in _STOPWORDS]
