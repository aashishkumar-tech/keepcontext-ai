"""Ask endpoint — enriched context query with LLM response.

Combines vector search, graph traversal, and LLM inference
to answer developer questions intelligently.

Endpoints:
    POST /api/v1/ask — Ask a question with full context pipeline
"""

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from keepcontext_ai.memory.schemas import MemoryQuery, MemoryType

router = APIRouter(prefix="/api/v1", tags=["ask"])


class AskRequest(BaseModel):
    """Request model for the enriched ask endpoint.

    Attributes:
        query: Natural language question.
        top_k: Maximum number of vector results.
        memory_type: Optional memory type filter.
        entity_name: Optional entity for graph lookup.
        use_llm: Whether to generate an LLM response.
    """

    model_config = ConfigDict(frozen=True)

    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Natural language question",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Max vector search results",
    )
    memory_type: MemoryType | None = Field(
        default=None,
        description="Optional memory type filter",
    )
    entity_name: str | None = Field(
        default=None,
        description="Optional entity name for graph context lookup",
    )
    use_llm: bool = Field(
        default=True,
        description="Whether to generate an LLM response",
    )


@router.post("/ask")
async def ask(
    request: Request,
    body: AskRequest,
) -> dict[str, Any]:
    """Ask a question with the full context pipeline.

    Pipeline:
        1. Vector search in ChromaDB for relevant memories.
        2. Graph traversal in Neo4j for entity relationships.
        3. LLM inference via Groq for intelligent answer.

    Args:
        request: The FastAPI request.
        body: The ask request with query and options.

    Returns:
        EnrichedContextResult with memories, graph context, and LLM answer.
    """
    retriever = request.app.state.retriever

    memory_query = MemoryQuery(
        query=body.query,
        top_k=body.top_k,
        memory_type=body.memory_type,
    )

    result = retriever.query_enriched(
        request=memory_query,
        entity_name=body.entity_name,
        use_llm=body.use_llm,
    )

    return {"data": result.model_dump()}
