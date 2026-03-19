"""Knowledge graph layer for KeepContext AI.

Provides Neo4j-backed storage for entity relationships,
enabling architecture reasoning and impact analysis.

Usage:
    from keepcontext_ai.graph import KnowledgeGraphClient, EntityCreate

    client = KnowledgeGraphClient(uri="bolt://localhost:7687")
    entity = EntityCreate(name="AuthService", entity_type="Service")
    stored = client.store_entity(entity)
"""

from keepcontext_ai.graph.entity_extractor import EntityExtractor
from keepcontext_ai.graph.neo4j_client import KnowledgeGraphClient
from keepcontext_ai.graph.schemas import (
    Entity,
    EntityCreate,
    GraphQuery,
    GraphResult,
    Relationship,
    RelationshipCreate,
    RelationshipType,
)

__all__ = [
    "Entity",
    "EntityCreate",
    "EntityExtractor",
    "GraphQuery",
    "GraphResult",
    "KnowledgeGraphClient",
    "Relationship",
    "RelationshipCreate",
    "RelationshipType",
]
