"""Extended schemas for context retrieval results.

Provides enriched context that combines vector search results
with knowledge graph relationships.
"""

from pydantic import BaseModel, ConfigDict, Field

from keepcontext_ai.graph.schemas import GraphResult
from keepcontext_ai.memory.schemas import MemoryResult


class EnrichedContextResult(BaseModel):
    """Combined result from vector search + graph traversal.

    Attributes:
        memory_results: Semantically similar memories from ChromaDB.
        graph_context: Related entities and relationships from Neo4j.
        llm_response: Optional LLM-generated answer using the context.
    """

    model_config = ConfigDict(frozen=True)

    memory_results: list[MemoryResult] = Field(
        default_factory=list,
        description="Vector search results from ChromaDB",
    )
    graph_context: GraphResult = Field(
        default_factory=lambda: GraphResult(entities=[], relationships=[]),
        description="Graph traversal results from Neo4j",
    )
    llm_response: str | None = Field(
        default=None,
        description="Optional LLM-generated answer",
    )
