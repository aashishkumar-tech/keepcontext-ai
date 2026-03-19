"""Unit tests for the enriched context retrieval pipeline."""

from unittest.mock import MagicMock

from keepcontext_ai.context.retrieval import ContextRetriever
from keepcontext_ai.context.schemas import EnrichedContextResult
from keepcontext_ai.exceptions import GraphError
from keepcontext_ai.graph.schemas import (
    Entity,
    GraphResult,
    Relationship,
    RelationshipType,
)
from keepcontext_ai.memory.schemas import (
    MemoryEntry,
    MemoryQuery,
    MemoryResult,
    MemoryType,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_EMBEDDING = [0.1] * 128


def _make_retriever(
    *,
    with_graph: bool = False,
    with_llm: bool = False,
) -> tuple[ContextRetriever, MagicMock, MagicMock, MagicMock | None, MagicMock | None]:
    """Create a ContextRetriever with mocked dependencies."""
    mock_chroma = MagicMock()
    mock_embeddings = MagicMock()
    mock_embeddings.generate.return_value = FAKE_EMBEDDING

    mock_graph = MagicMock() if with_graph else None
    mock_llm = MagicMock() if with_llm else None

    retriever = ContextRetriever(
        chroma_client=mock_chroma,
        embedding_service=mock_embeddings,
        graph_client=mock_graph,
        llm_service=mock_llm,
    )
    return retriever, mock_chroma, mock_embeddings, mock_graph, mock_llm


def _sample_memory_result() -> MemoryResult:
    entry = MemoryEntry(
        id="1",
        content="JWT auth",
        memory_type=MemoryType.DECISION,
        created_at="2025-01-01T00:00:00+00:00",
    )
    return MemoryResult(entry=entry, score=0.9)


def _sample_graph_result() -> GraphResult:
    return GraphResult(
        entities=[Entity(name="AuthService", entity_type="Service")],
        relationships=[
            Relationship(
                source="AuthService",
                target="UserModel",
                relationship_type=RelationshipType.USES,
            )
        ],
    )


# ---------------------------------------------------------------------------
# query_enriched - vector only
# ---------------------------------------------------------------------------


class TestQueryEnrichedVectorOnly:
    """Tests for query_enriched without graph/LLM."""

    def test_returns_enriched_result(self) -> None:
        retriever, mock_chroma, _, _, _ = _make_retriever()
        mock_chroma.query.return_value = [_sample_memory_result()]

        request = MemoryQuery(query="How does auth work?")
        result = retriever.query_enriched(request)

        assert isinstance(result, EnrichedContextResult)
        assert len(result.memory_results) == 1
        assert result.llm_response is None
        assert result.graph_context.entities == []

    def test_empty_results(self) -> None:
        retriever, mock_chroma, _, _, _ = _make_retriever()
        mock_chroma.query.return_value = []

        request = MemoryQuery(query="unknown topic")
        result = retriever.query_enriched(request)

        assert result.memory_results == []


# ---------------------------------------------------------------------------
# query_enriched - with graph
# ---------------------------------------------------------------------------


class TestQueryEnrichedWithGraph:
    """Tests for query_enriched with graph context."""

    def test_graph_context_included(self) -> None:
        retriever, mock_chroma, _, mock_graph, _ = _make_retriever(with_graph=True)
        mock_chroma.query.return_value = [_sample_memory_result()]
        mock_graph.query_relationships.return_value = _sample_graph_result()

        request = MemoryQuery(query="auth?")
        result = retriever.query_enriched(request, entity_name="AuthService")

        assert len(result.graph_context.entities) == 1
        assert result.graph_context.entities[0].name == "AuthService"

    def test_graph_without_entity_name_skips(self) -> None:
        retriever, mock_chroma, _, mock_graph, _ = _make_retriever(with_graph=True)
        mock_chroma.query.return_value = []

        request = MemoryQuery(query="test")
        result = retriever.query_enriched(request)

        mock_graph.query_relationships.assert_not_called()
        assert result.graph_context.entities == []

    def test_graph_error_degrades_gracefully(self) -> None:
        retriever, mock_chroma, _, mock_graph, _ = _make_retriever(with_graph=True)
        mock_chroma.query.return_value = [_sample_memory_result()]
        mock_graph.query_relationships.side_effect = GraphError(
            message="Neo4j down", code="graph_connection_error"
        )

        request = MemoryQuery(query="test")
        result = retriever.query_enriched(request, entity_name="Auth")

        assert len(result.memory_results) == 1
        assert result.graph_context.entities == []


# ---------------------------------------------------------------------------
# query_enriched - with LLM
# ---------------------------------------------------------------------------


class TestQueryEnrichedWithLLM:
    """Tests for query_enriched with LLM response."""

    def test_llm_response_included(self) -> None:
        retriever, mock_chroma, _, _, mock_llm = _make_retriever(with_llm=True)
        mock_chroma.query.return_value = [_sample_memory_result()]
        mock_llm.generate_with_context.return_value = "Auth uses JWT tokens"

        request = MemoryQuery(query="auth?")
        result = retriever.query_enriched(request)

        assert result.llm_response == "Auth uses JWT tokens"

    def test_llm_disabled_via_flag(self) -> None:
        retriever, mock_chroma, _, _, mock_llm = _make_retriever(with_llm=True)
        mock_chroma.query.return_value = []

        request = MemoryQuery(query="test")
        result = retriever.query_enriched(request, use_llm=False)

        mock_llm.generate_with_context.assert_not_called()
        assert result.llm_response is None

    def test_llm_error_degrades_gracefully(self) -> None:
        retriever, mock_chroma, _, _, mock_llm = _make_retriever(with_llm=True)
        mock_chroma.query.return_value = []
        mock_llm.generate_with_context.side_effect = RuntimeError("LLM down")

        request = MemoryQuery(query="test")
        result = retriever.query_enriched(request)

        assert result.llm_response is None


# ---------------------------------------------------------------------------
# query_enriched - full pipeline
# ---------------------------------------------------------------------------


class TestQueryEnrichedFullPipeline:
    """Tests for the full vector + graph + LLM pipeline."""

    def test_full_pipeline(self) -> None:
        retriever, mock_chroma, _, mock_graph, mock_llm = _make_retriever(
            with_graph=True, with_llm=True
        )
        mock_chroma.query.return_value = [_sample_memory_result()]
        mock_graph.query_relationships.return_value = _sample_graph_result()
        mock_llm.generate_with_context.return_value = "Full answer"

        request = MemoryQuery(query="auth?")
        result = retriever.query_enriched(request, entity_name="AuthService")

        assert len(result.memory_results) == 1
        assert len(result.graph_context.entities) == 1
        assert result.llm_response == "Full answer"
