"""Context retrieval engine for KeepContext AI.

Orchestrates the full query pipeline:
    Phase 1: User query → embedding → ChromaDB search → ranked results.
    Phase 2: + Neo4j graph traversal + Groq LLM response.

This is the core "ask your project a question" capability.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from keepcontext_ai.context.schemas import EnrichedContextResult
from keepcontext_ai.embeddings import EmbeddingService
from keepcontext_ai.exceptions import (
    ContextError,
    EmbeddingError,
    GraphError,
    MemoryError,
)
from keepcontext_ai.memory import ChromaMemoryClient, MemoryQuery, MemoryResult

if TYPE_CHECKING:
    from keepcontext_ai.graph import KnowledgeGraphClient
    from keepcontext_ai.llm import GroqLLMService


class ContextRetriever:
    """Retrieves relevant project context using semantic search.

    Combines vector search (ChromaDB), graph traversal (Neo4j),
    and LLM inference (Groq) to provide intelligent answers.

    Attributes:
        _chroma: ChromaDB client for vector search.
        _embeddings: Service for generating query embeddings.
        _graph: Optional Neo4j client for graph context.
        _llm: Optional Groq LLM service for intelligent responses.
    """

    def __init__(
        self,
        chroma_client: ChromaMemoryClient,
        embedding_service: EmbeddingService,
        graph_client: KnowledgeGraphClient | None = None,
        llm_service: GroqLLMService | None = None,
    ) -> None:
        """Initialize the context retriever with its dependencies.

        Args:
            chroma_client: ChromaDB client for memory operations.
            embedding_service: Service for generating embeddings.
            graph_client: Optional Neo4j client for graph context.
            llm_service: Optional Groq service for LLM responses.
        """
        self._chroma = chroma_client
        self._embeddings = embedding_service
        self._graph = graph_client
        self._llm = llm_service

    def query(self, request: MemoryQuery) -> list[MemoryResult]:
        """Query project memory with natural language (Phase 1 — vector only).

        Pipeline:
            1. Generate embedding from query text.
            2. Search ChromaDB for similar entries.
            3. Return ranked results with relevance scores.

        Args:
            request: The query request containing the search text,
                top_k limit, and optional memory type filter.

        Returns:
            List of MemoryResult objects sorted by relevance.

        Raises:
            ContextError: If the query pipeline fails at any stage.
        """
        try:
            query_embedding = self._embeddings.generate(request.query)
        except EmbeddingError as e:
            raise ContextError(
                message=f"Failed to generate embedding for query: {request.query[:50]}",
                code="context_embedding_error",
            ) from e

        try:
            results = self._chroma.query(
                embedding=query_embedding,
                top_k=request.top_k,
                memory_type=request.memory_type,
            )
        except MemoryError as e:
            raise ContextError(
                message="Failed to search memory for relevant context",
                code="context_search_error",
            ) from e

        return results

    def query_enriched(
        self,
        request: MemoryQuery,
        entity_name: str | None = None,
        use_llm: bool = True,
    ) -> EnrichedContextResult:
        """Query with full context pipeline (Phase 2 — vector + graph + LLM).

        Pipeline:
            1. Generate embedding from query text.
            2. Search ChromaDB for similar entries.
            3. Optionally query Neo4j for related graph context.
            4. Optionally send context to Groq LLM for intelligent answer.

        Args:
            request: The query request.
            entity_name: Optional entity name for graph lookup.
            use_llm: Whether to generate an LLM response.

        Returns:
            EnrichedContextResult with memories, graph, and optional LLM answer.

        Raises:
            ContextError: If the query pipeline fails.
        """
        # Step 1+2: Vector search (same as query())
        memory_results = self.query(request)

        # Step 3: Graph context (optional)
        graph_result = None
        if self._graph and entity_name:
            try:
                from keepcontext_ai.graph.schemas import GraphQuery

                graph_query = GraphQuery(
                    entity_name=entity_name,
                    direction="both",
                    depth=2,
                )
                graph_result = self._graph.query_relationships(graph_query)
            except GraphError:
                # Graph is optional — don't fail the whole query
                graph_result = None

        # Step 4: LLM response (optional)
        llm_response = None
        if self._llm and use_llm:
            try:
                llm_response = self._llm.generate_with_context(
                    query=request.query,
                    memory_results=memory_results if memory_results else None,
                    graph_result=graph_result,
                )
            except Exception:
                # LLM is optional — don't fail the whole query
                llm_response = None

        from keepcontext_ai.graph.schemas import GraphResult

        return EnrichedContextResult(
            memory_results=memory_results,
            graph_context=graph_result if graph_result is not None else GraphResult(),
            llm_response=llm_response,
        )
