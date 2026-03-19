"""Unit tests for knowledge graph Pydantic schemas."""

import pytest
from pydantic import ValidationError

from keepcontext_ai.graph.schemas import (
    Entity,
    EntityCreate,
    GraphQuery,
    GraphResult,
    Relationship,
    RelationshipCreate,
    RelationshipType,
)

# ---------------------------------------------------------------------------
# RelationshipType enum
# ---------------------------------------------------------------------------


class TestRelationshipType:
    """Tests for the RelationshipType enum."""

    def test_all_values_exist(self) -> None:
        expected = {
            "USES",
            "DEPENDS_ON",
            "IMPLEMENTS",
            "CONTAINS",
            "PROTECTS",
            "CALLS",
            "EXTENDS",
            "RELATED_TO",
        }
        assert {rt.value for rt in RelationshipType} == expected

    def test_string_enum(self) -> None:
        assert RelationshipType.USES == "USES"
        assert isinstance(RelationshipType.DEPENDS_ON, str)


# ---------------------------------------------------------------------------
# EntityCreate
# ---------------------------------------------------------------------------


class TestEntityCreate:
    """Tests for the EntityCreate model."""

    def test_valid_entity_create(self) -> None:
        entity = EntityCreate(name="AuthService", entity_type="Service")
        assert entity.name == "AuthService"
        assert entity.entity_type == "Service"
        assert entity.properties == {}

    def test_with_properties(self) -> None:
        entity = EntityCreate(
            name="UserModel",
            entity_type="Model",
            properties={"module": "users"},
        )
        assert entity.properties == {"module": "users"}

    def test_frozen(self) -> None:
        entity = EntityCreate(name="X", entity_type="Y")
        with pytest.raises(ValidationError):
            entity.name = "Z"  # type: ignore[misc]

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EntityCreate(name="", entity_type="Service")

    def test_name_max_length(self) -> None:
        with pytest.raises(ValidationError):
            EntityCreate(name="a" * 501, entity_type="Service")

    def test_empty_entity_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EntityCreate(name="X", entity_type="")


# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------


class TestEntity:
    """Tests for the Entity model."""

    def test_valid_entity(self) -> None:
        entity = Entity(name="AuthService", entity_type="Service")
        assert entity.name == "AuthService"
        assert entity.properties == {}

    def test_frozen(self) -> None:
        entity = Entity(name="X", entity_type="Y")
        with pytest.raises(ValidationError):
            entity.name = "Z"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RelationshipCreate
# ---------------------------------------------------------------------------


class TestRelationshipCreate:
    """Tests for the RelationshipCreate model."""

    def test_valid_relationship_create(self) -> None:
        rel = RelationshipCreate(
            source="AuthService",
            target="UserModel",
            relationship_type=RelationshipType.USES,
        )
        assert rel.source == "AuthService"
        assert rel.target == "UserModel"
        assert rel.relationship_type == RelationshipType.USES

    def test_with_properties(self) -> None:
        rel = RelationshipCreate(
            source="A",
            target="B",
            relationship_type=RelationshipType.DEPENDS_ON,
            properties={"version": "2.0"},
        )
        assert rel.properties == {"version": "2.0"}

    def test_empty_source_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RelationshipCreate(
                source="",
                target="B",
                relationship_type=RelationshipType.USES,
            )


# ---------------------------------------------------------------------------
# Relationship
# ---------------------------------------------------------------------------


class TestRelationship:
    """Tests for the Relationship model."""

    def test_valid_relationship(self) -> None:
        rel = Relationship(
            source="A",
            target="B",
            relationship_type=RelationshipType.CALLS,
        )
        assert rel.source == "A"
        assert rel.relationship_type == RelationshipType.CALLS

    def test_frozen(self) -> None:
        rel = Relationship(
            source="A",
            target="B",
            relationship_type=RelationshipType.CALLS,
        )
        with pytest.raises(ValidationError):
            rel.source = "C"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# GraphQuery
# ---------------------------------------------------------------------------


class TestGraphQuery:
    """Tests for the GraphQuery model."""

    def test_defaults(self) -> None:
        q = GraphQuery(entity_name="AuthService")
        assert q.direction == "outgoing"
        assert q.depth == 1
        assert q.relationship_type is None

    def test_valid_directions(self) -> None:
        for direction in ("outgoing", "incoming", "both"):
            q = GraphQuery(entity_name="X", direction=direction)
            assert q.direction == direction

    def test_invalid_direction_rejected(self) -> None:
        with pytest.raises(ValidationError):
            GraphQuery(entity_name="X", direction="sideways")

    def test_depth_bounds(self) -> None:
        q = GraphQuery(entity_name="X", depth=5)
        assert q.depth == 5

        with pytest.raises(ValidationError):
            GraphQuery(entity_name="X", depth=0)

        with pytest.raises(ValidationError):
            GraphQuery(entity_name="X", depth=6)

    def test_with_relationship_type(self) -> None:
        q = GraphQuery(
            entity_name="X",
            relationship_type=RelationshipType.DEPENDS_ON,
        )
        assert q.relationship_type == RelationshipType.DEPENDS_ON


# ---------------------------------------------------------------------------
# GraphResult
# ---------------------------------------------------------------------------


class TestGraphResult:
    """Tests for the GraphResult model."""

    def test_empty_result(self) -> None:
        r = GraphResult()
        assert r.entities == []
        assert r.relationships == []

    def test_with_data(self) -> None:
        entity = Entity(name="A", entity_type="Service")
        rel = Relationship(
            source="A",
            target="B",
            relationship_type=RelationshipType.USES,
        )
        r = GraphResult(entities=[entity], relationships=[rel])
        assert len(r.entities) == 1
        assert len(r.relationships) == 1

    def test_frozen(self) -> None:
        r = GraphResult()
        with pytest.raises(ValidationError):
            r.entities = []  # type: ignore[misc]
