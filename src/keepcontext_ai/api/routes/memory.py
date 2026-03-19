"""Memory CRUD endpoints.

Provides REST endpoints for storing, retrieving, listing,
and deleting memory entries.

Endpoints:
    POST   /api/v1/memory          — Store a new memory entry
    GET    /api/v1/memory          — List memory entries (with pagination)
    GET    /api/v1/memory/{id}     — Get a specific memory entry
    DELETE /api/v1/memory/{id}     — Delete a memory entry
"""

import logging
from typing import Any

from fastapi import APIRouter, Query, Request, Response, status

from keepcontext_ai.memory.schemas import MemoryCreate, MemoryType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def store_memory(
    request: Request,
    body: MemoryCreate,
) -> dict[str, Any]:
    """Store a new memory entry.

    Generates an embedding for the content and stores both
    the text and vector in ChromaDB.

    Args:
        request: The FastAPI request (provides access to app services).
        body: The memory entry to store.

    Returns:
        The stored memory entry wrapped in a data envelope.
    """
    embedding_service = request.app.state.embeddings
    chroma_client = request.app.state.chroma

    embedding = embedding_service.generate(body.content)
    entry = chroma_client.store(body, embedding)

    # Trigger entity extraction if graph + LLM are available
    extraction_result = None
    graph_client = getattr(request.app.state, "graph", None)
    llm_service = getattr(request.app.state, "llm", None)
    if graph_client is not None and llm_service is not None:
        try:
            from keepcontext_ai.graph.entity_extractor import EntityExtractor

            extractor = EntityExtractor(
                llm_service=llm_service,
                graph_client=graph_client,
            )
            extraction_result = extractor.extract_and_store(body.content)
            logger.info(
                "Extracted %d entities, %d relationships from memory %s",
                extraction_result["entities"],
                extraction_result["relationships"],
                entry.id,
            )
        except Exception:
            logger.warning("Entity extraction failed for memory %s", entry.id)

    response_data: dict[str, Any] = {"data": entry.model_dump()}
    if extraction_result is not None:
        response_data["meta"] = {"extraction": extraction_result}

    return response_data


@router.get("")
async def list_memories(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100, description="Max entries to return"),
    offset: int = Query(default=0, ge=0, description="Number of entries to skip"),
    memory_type: MemoryType | None = Query(
        default=None, description="Filter by memory type"
    ),
) -> dict[str, Any]:
    """List memory entries with pagination and optional filtering.

    Args:
        request: The FastAPI request.
        limit: Maximum number of entries to return.
        offset: Number of entries to skip.
        memory_type: Optional filter by memory type.

    Returns:
        List of memory entries with pagination metadata.
    """
    chroma_client = request.app.state.chroma

    entries = chroma_client.list_entries(
        limit=limit,
        offset=offset,
        memory_type=memory_type,
    )
    total = chroma_client.count()

    return {
        "data": [entry.model_dump() for entry in entries],
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    }


@router.get("/{memory_id}")
async def get_memory(
    request: Request,
    memory_id: str,
) -> dict[str, Any]:
    """Retrieve a specific memory entry by ID.

    Args:
        request: The FastAPI request.
        memory_id: The unique identifier of the memory entry.

    Returns:
        The memory entry wrapped in a data envelope.
    """
    chroma_client = request.app.state.chroma
    entry = chroma_client.get(memory_id)

    return {"data": entry.model_dump()}


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    request: Request,
    memory_id: str,
) -> Response:
    """Delete a memory entry by ID.

    Args:
        request: The FastAPI request.
        memory_id: The unique identifier of the entry to delete.

    Returns:
        204 No Content on success.
    """
    chroma_client = request.app.state.chroma
    chroma_client.delete(memory_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
