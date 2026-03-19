"""Pydantic models for the knowledge graph layer.

Defines data contracts for entities, relationships, and graph queries
in KeepContext AI's Neo4j knowledge graph.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class RelationshipType(str, Enum):
    """Types of relationships between entities in the knowledge graph."""

    USES = "USES"
    DEPENDS_ON = "DEPENDS_ON"
    IMPLEMENTS = "IMPLEMENTS"
    CONTAINS = "CONTAINS"
    PROTECTS = "PROTECTS"
    CALLS = "CALLS"
    EXTENDS = "EXTENDS"
    RELATED_TO = "RELATED_TO"


class EntityCreate(BaseModel):
    """Request model for creating a graph entity (node).

    Attributes:
        name: Unique name for the entity.
        entity_type: Category (e.g., 'Service', 'Model', 'Feature').
        properties: Optional key-value metadata.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Unique entity name",
    )
    entity_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Entity category (e.g., Service, Model, Feature)",
    )
    properties: dict[str, str] = Field(
        default_factory=dict,
        description="Optional key-value metadata",
    )


class Entity(BaseModel):
    """Full entity as stored in the graph database.

    Attributes:
        name: Unique name for the entity.
        entity_type: Category of the entity.
        properties: Key-value metadata.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Unique entity name")
    entity_type: str = Field(..., description="Entity category")
    properties: dict[str, str] = Field(
        default_factory=dict,
        description="Key-value metadata",
    )


class RelationshipCreate(BaseModel):
    """Request model for creating a relationship between two entities.

    Attributes:
        source: Name of the source entity.
        target: Name of the target entity.
        relationship_type: Type of the relationship.
        properties: Optional key-value metadata on the edge.
    """

    model_config = ConfigDict(frozen=True)

    source: str = Field(
        ...,
        min_length=1,
        description="Source entity name",
    )
    target: str = Field(
        ...,
        min_length=1,
        description="Target entity name",
    )
    relationship_type: RelationshipType = Field(
        ...,
        description="Type of relationship",
    )
    properties: dict[str, str] = Field(
        default_factory=dict,
        description="Optional edge metadata",
    )


class Relationship(BaseModel):
    """Full relationship as stored in the graph database.

    Attributes:
        source: Source entity name.
        target: Target entity name.
        relationship_type: Type of the relationship.
        properties: Edge metadata.
    """

    model_config = ConfigDict(frozen=True)

    source: str = Field(..., description="Source entity name")
    target: str = Field(..., description="Target entity name")
    relationship_type: RelationshipType = Field(..., description="Relationship type")
    properties: dict[str, str] = Field(
        default_factory=dict,
        description="Edge metadata",
    )


class GraphQuery(BaseModel):
    """Request model for querying the knowledge graph.

    Attributes:
        entity_name: Name of the entity to query from.
        relationship_type: Optional filter by relationship type.
        direction: Query direction — 'outgoing', 'incoming', or 'both'.
        depth: How many hops to traverse (1 = direct only).
    """

    model_config = ConfigDict(frozen=True)

    entity_name: str = Field(
        ...,
        min_length=1,
        description="Entity to query from",
    )
    relationship_type: RelationshipType | None = Field(
        default=None,
        description="Optional filter by relationship type",
    )
    direction: str = Field(
        default="outgoing",
        pattern="^(outgoing|incoming|both)$",
        description="Query direction",
    )
    depth: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Number of hops to traverse",
    )


class GraphResult(BaseModel):
    """Result from a graph query.

    Attributes:
        entities: List of discovered entities.
        relationships: List of discovered relationships.
    """

    model_config = ConfigDict(frozen=True)

    entities: list[Entity] = Field(
        default_factory=list,
        description="Discovered entities",
    )
    relationships: list[Relationship] = Field(
        default_factory=list,
        description="Discovered relationships",
    )
