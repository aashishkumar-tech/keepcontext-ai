"""Unit tests for quality evaluation metrics."""

from keepcontext_ai.evaluation.metrics import (
    groundedness_score,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class TestRetrievalMetrics:
    """Tests for retrieval metric helpers."""

    def test_precision_at_k(self) -> None:
        score = precision_at_k(["a", "b", "c"], {"a", "x"}, 3)
        assert score == 1 / 3

    def test_recall_at_k(self) -> None:
        score = recall_at_k(["a", "b", "c"], {"a", "x"}, 3)
        assert score == 0.5

    def test_recall_when_no_relevant_ids(self) -> None:
        score = recall_at_k(["a", "b"], set(), 2)
        assert score == 1.0

    def test_reciprocal_rank(self) -> None:
        score = reciprocal_rank(["x", "a", "b"], {"a"})
        assert score == 0.5


class TestGroundednessMetric:
    """Tests for lexical groundedness scoring."""

    def test_groundedness_overlap(self) -> None:
        score = groundedness_score(
            response="Authentication uses token validation",
            evidence_text="Auth token validation with JWT",
        )
        assert 0.3 <= score <= 1.0

    def test_groundedness_without_response(self) -> None:
        score = groundedness_score(response=None, evidence_text="some evidence")
        assert score == 0.0

    def test_groundedness_without_evidence(self) -> None:
        score = groundedness_score(response="A response", evidence_text="")
        assert score == 0.0
