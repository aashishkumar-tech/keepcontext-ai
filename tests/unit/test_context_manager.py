"""Unit tests for the context manager agent node."""

from __future__ import annotations

from unittest.mock import MagicMock

from keepcontext_ai.agents.context_manager import context_manager_node
from keepcontext_ai.context.schemas import EnrichedContextResult
from keepcontext_ai.graph.schemas import GraphResult
from keepcontext_ai.memory.schemas import MemoryEntry, MemoryResult, MemoryType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_retriever_mock(
    memories: list[MemoryResult] | None = None,
    graph: GraphResult | None = None,
) -> MagicMock:
    """Build a mock ContextRetriever with canned responses."""
    mock = MagicMock()
    enriched = EnrichedContextResult(
        memory_results=memories or [],
        graph_context=graph or GraphResult(),
        llm_response=None,
    )
    mock.query_enriched.return_value = enriched
    return mock


def _make_memory_result(content: str, score: float = 0.9) -> MemoryResult:
    entry = MemoryEntry(
        id="test-id",
        content=content,
        memory_type=MemoryType.DECISION,
        metadata={},
        created_at="2025-01-01T00:00:00+00:00",
    )
    return MemoryResult(entry=entry, score=score)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestContextManagerNode:
    """Tests for context_manager_node."""

    def test_returns_context_results(self) -> None:
        retriever = _make_retriever_mock(
            memories=[_make_memory_result("JWT auth is used")]
        )
        state = {"goal": "How does Authentication work?"}
        result = context_manager_node(state, retriever=retriever)

        assert len(result["context_results"]) == 1
        assert result["context_results"][0]["content"] == "JWT auth is used"
        retriever.query_enriched.assert_called_once()

    def test_entity_extraction_from_capitalised_word(self) -> None:
        retriever = _make_retriever_mock()
        state = {"goal": "Explain the UserService module"}
        context_manager_node(state, retriever=retriever)

        call_kwargs = retriever.query_enriched.call_args
        assert call_kwargs.kwargs.get("entity_name") == "UserService"

    def test_no_entity_for_lowercase_goal(self) -> None:
        retriever = _make_retriever_mock()
        state = {"goal": "how does login work"}
        context_manager_node(state, retriever=retriever)

        call_kwargs = retriever.query_enriched.call_args
        assert call_kwargs.kwargs.get("entity_name") is None

    def test_empty_goal(self) -> None:
        retriever = _make_retriever_mock()
        state = {"goal": ""}
        result = context_manager_node(state, retriever=retriever)

        assert "context_results" in result
        assert "graph_context" in result

    def test_retriever_exception_graceful(self) -> None:
        retriever = MagicMock()
        retriever.query_enriched.side_effect = RuntimeError("connection failed")

        state = {"goal": "test"}
        result = context_manager_node(state, retriever=retriever)

        assert result["context_results"] == []
        assert result["graph_context"]["entities"] == []

    def test_preserves_existing_state(self) -> None:
        retriever = _make_retriever_mock()
        state = {"goal": "test", "max_iterations": 5}
        result = context_manager_node(state, retriever=retriever)

        assert result["max_iterations"] == 5
        assert result["goal"] == "test"
