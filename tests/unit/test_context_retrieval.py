"""Unit tests for ContextRetriever."""

from unittest.mock import MagicMock

import pytest

from keepcontext_ai.context.retrieval import ContextRetriever
from keepcontext_ai.exceptions import ContextError, EmbeddingError, MemoryError
from keepcontext_ai.memory.schemas import (
    MemoryEntry,
    MemoryQuery,
    MemoryResult,
    MemoryType,
)

FAKE_EMBEDDING = [0.1] * 128


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_retriever(
    mock_chroma: MagicMock | None = None,
    mock_embeddings: MagicMock | None = None,
) -> ContextRetriever:
    """Create a ContextRetriever with mocked dependencies."""
    chroma = mock_chroma or MagicMock()
    embeddings = mock_embeddings or MagicMock()
    embeddings.generate.return_value = FAKE_EMBEDDING
    return ContextRetriever(chroma_client=chroma, embedding_service=embeddings)


def _sample_result() -> MemoryResult:
    """Build a sample MemoryResult."""
    entry = MemoryEntry(
        id="uuid-1",
        content="Auth uses JWT",
        memory_type=MemoryType.DECISION,
        created_at="2025-01-01T00:00:00+00:00",
    )
    return MemoryResult(entry=entry, score=0.9)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestContextRetrieverInit:
    """Tests for ContextRetriever initialization."""

    def test_init_stores_dependencies(self) -> None:
        mock_chroma = MagicMock()
        mock_embeddings = MagicMock()

        retriever = ContextRetriever(
            chroma_client=mock_chroma,
            embedding_service=mock_embeddings,
        )

        assert retriever._chroma is mock_chroma
        assert retriever._embeddings is mock_embeddings


class TestContextRetrieverQuery:
    """Tests for the query() method."""

    def test_query_returns_results(self) -> None:
        mock_chroma = MagicMock()
        mock_chroma.query.return_value = [_sample_result()]

        retriever = _make_retriever(mock_chroma=mock_chroma)
        request = MemoryQuery(query="How does auth work?")

        results = retriever.query(request)

        assert len(results) == 1
        assert results[0].entry.content == "Auth uses JWT"
        assert results[0].score == 0.9

    def test_query_generates_embedding_from_query_text(self) -> None:
        mock_embeddings = MagicMock()
        mock_embeddings.generate.return_value = FAKE_EMBEDDING
        mock_chroma = MagicMock()
        mock_chroma.query.return_value = []

        retriever = ContextRetriever(
            chroma_client=mock_chroma,
            embedding_service=mock_embeddings,
        )
        request = MemoryQuery(query="Search this")

        retriever.query(request)

        mock_embeddings.generate.assert_called_once_with("Search this")

    def test_query_passes_top_k_and_type_filter(self) -> None:
        mock_chroma = MagicMock()
        mock_chroma.query.return_value = []

        retriever = _make_retriever(mock_chroma=mock_chroma)
        request = MemoryQuery(
            query="search",
            top_k=10,
            memory_type=MemoryType.CODE,
        )

        retriever.query(request)

        mock_chroma.query.assert_called_once_with(
            embedding=FAKE_EMBEDDING,
            top_k=10,
            memory_type=MemoryType.CODE,
        )

    def test_query_empty_results(self) -> None:
        mock_chroma = MagicMock()
        mock_chroma.query.return_value = []

        retriever = _make_retriever(mock_chroma=mock_chroma)
        request = MemoryQuery(query="nothing here")

        results = retriever.query(request)

        assert results == []

    def test_embedding_failure_raises_context_error(self) -> None:
        mock_embeddings = MagicMock()
        mock_embeddings.generate.side_effect = EmbeddingError("API down")

        retriever = _make_retriever(mock_embeddings=mock_embeddings)
        request = MemoryQuery(query="search")

        with pytest.raises(ContextError) as exc_info:
            retriever.query(request)
        assert exc_info.value.code == "context_embedding_error"
        assert exc_info.value.__cause__ is not None

    def test_memory_failure_raises_context_error(self) -> None:
        mock_chroma = MagicMock()
        mock_chroma.query.side_effect = MemoryError("DB down")

        retriever = _make_retriever(mock_chroma=mock_chroma)
        request = MemoryQuery(query="search")

        with pytest.raises(ContextError) as exc_info:
            retriever.query(request)
        assert exc_info.value.code == "context_search_error"
        assert exc_info.value.__cause__ is not None
