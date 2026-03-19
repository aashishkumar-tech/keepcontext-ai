"""Context query endpoint.

Provides semantic search over stored project memories.

Endpoints:
    POST /api/v1/context/query — Query context with natural language
"""

from typing import Any

from fastapi import APIRouter, Request

from keepcontext_ai.memory.schemas import MemoryQuery

router = APIRouter(prefix="/api/v1/context", tags=["context"])


@router.post("/query")
async def query_context(
    request: Request,
    body: MemoryQuery,
) -> dict[str, Any]:
    """Query project memory with natural language.

    Takes a natural language question, generates an embedding,
    and searches ChromaDB for semantically similar memories.

    Args:
        request: The FastAPI request (provides access to app services).
        body: The query request with search text and parameters.

    Returns:
        List of matching memory entries with relevance scores.
    """
    retriever = request.app.state.retriever

    results = retriever.query(body)

    return {
        "data": [result.model_dump() for result in results],
    }
