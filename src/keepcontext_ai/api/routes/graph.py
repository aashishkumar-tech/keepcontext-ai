"""Knowledge graph endpoints.

Provides REST endpoints for managing entities, relationships,
and querying the knowledge graph.

Endpoints:
    POST   /api/v1/graph/entities           — Create/update an entity
    GET    /api/v1/graph/entities/{name}     — Get an entity by name
    POST   /api/v1/graph/relationships       — Create a relationship
    POST   /api/v1/graph/query               — Query relationships
    GET    /api/v1/graph/dependencies/{name} — Get entity dependencies
    POST   /api/v1/graph/impact              — Run impact analysis
    GET    /api/v1/graph/stats               — Get graph statistics
"""

from typing import Any

from fastapi import APIRouter, Request, status

from keepcontext_ai.graph.schemas import (
    EntityCreate,
    GraphQuery,
    RelationshipCreate,
)

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


@router.post("/entities", status_code=status.HTTP_201_CREATED)
async def create_entity(
    request: Request,
    body: EntityCreate,
) -> dict[str, Any]:
    """Create or update an entity in the knowledge graph.

    Uses MERGE semantics — updates properties if entity already exists.

    Args:
        request: The FastAPI request.
        body: The entity to create/update.

    Returns:
        The stored entity wrapped in a data envelope.
    """
    graph_client = request.app.state.graph
    entity = graph_client.store_entity(body)
    return {"data": entity.model_dump()}


@router.get("/entities/{name}")
async def get_entity(
    request: Request,
    name: str,
) -> dict[str, Any]:
    """Retrieve an entity by name.

    Args:
        request: The FastAPI request.
        name: The entity name.

    Returns:
        The entity wrapped in a data envelope.
    """
    graph_client = request.app.state.graph
    entity = graph_client.get_entity(name)
    return {"data": entity.model_dump()}


@router.post("/relationships", status_code=status.HTTP_201_CREATED)
async def create_relationship(
    request: Request,
    body: RelationshipCreate,
) -> dict[str, Any]:
    """Create a relationship between two entities.

    Auto-creates source/target entities if they don't exist.

    Args:
        request: The FastAPI request.
        body: The relationship to create.

    Returns:
        The stored relationship wrapped in a data envelope.
    """
    graph_client = request.app.state.graph
    relationship = graph_client.store_relationship(body)
    return {"data": relationship.model_dump()}


@router.post("/query")
async def query_graph(
    request: Request,
    body: GraphQuery,
) -> dict[str, Any]:
    """Query the knowledge graph for relationships.

    Args:
        request: The FastAPI request.
        body: The graph query parameters.

    Returns:
        GraphResult with entities and relationships.
    """
    graph_client = request.app.state.graph
    result = graph_client.query_relationships(body)
    return {"data": result.model_dump()}


@router.get("/dependencies/{name}")
async def get_dependencies(
    request: Request,
    name: str,
) -> dict[str, Any]:
    """Get all dependencies for an entity.

    Args:
        request: The FastAPI request.
        name: The entity name to check dependencies for.

    Returns:
        GraphResult with dependent entities and relationships.
    """
    graph_client = request.app.state.graph
    result = graph_client.get_dependencies(name)
    return {"data": result.model_dump()}


@router.post("/impact")
async def impact_analysis(
    request: Request,
    body: GraphQuery,
) -> dict[str, Any]:
    """Determine what would be affected if an entity changes.

    Args:
        request: The FastAPI request.
        body: Query with entity_name for impact analysis.

    Returns:
        GraphResult with affected entities and relationships.
    """
    graph_client = request.app.state.graph
    result = graph_client.impact_analysis(body.entity_name)
    return {"data": result.model_dump()}


@router.get("/stats")
async def graph_stats(
    request: Request,
) -> dict[str, Any]:
    """Get knowledge graph statistics.

    Returns:
        Total entity count.
    """
    graph_client = request.app.state.graph
    count = graph_client.count_entities()
    return {"data": {"entity_count": count}}
