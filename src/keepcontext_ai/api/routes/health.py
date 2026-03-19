"""Health check endpoint.

Provides application health status including ChromaDB connectivity.
"""

from typing import Any

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(request: Request) -> dict[str, Any]:
    """Check application health and service connectivity.

    Returns:
        Health status including app version and ChromaDB connection state.
    """
    settings = request.app.state.settings
    chroma_status = "disconnected"

    try:
        chroma_client = request.app.state.chroma
        chroma_client.count()
        chroma_status = "connected"
    except Exception:
        chroma_status = "disconnected"

    # Neo4j status
    neo4j_status = "disabled"
    graph_client = getattr(request.app.state, "graph", None)
    if graph_client is not None:
        try:
            graph_client.count_entities()
            neo4j_status = "connected"
        except Exception:
            neo4j_status = "disconnected"

    # Groq LLM status
    llm_status = "disabled"
    llm_service = getattr(request.app.state, "llm", None)
    if llm_service is not None:
        llm_status = "configured"

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "chroma": chroma_status,
        "neo4j": neo4j_status,
        "llm": llm_status,
    }
