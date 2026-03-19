"""Unit tests for KnowledgeGraphClient (Neo4j)."""

from unittest.mock import MagicMock, patch

import pytest

from keepcontext_ai.exceptions import GraphError
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client() -> tuple[KnowledgeGraphClient, MagicMock]:
    """Create a KnowledgeGraphClient with a mocked Neo4j driver."""
    with patch("keepcontext_ai.graph.neo4j_client.GraphDatabase") as mock_gdb:
        mock_driver = MagicMock()
        mock_gdb.driver.return_value = mock_driver
        client = KnowledgeGraphClient(
            uri="bolt://test:7687",
            user="neo4j",
            password="test",
        )
    return client, mock_driver


def _mock_session_run(mock_driver: MagicMock, records: list[dict]) -> MagicMock:
    """Set up a mock session.run() that returns the given records."""
    mock_session = MagicMock()
    mock_result = MagicMock()

    if len(records) == 1:
        mock_result.single.return_value = records[0]
    elif len(records) == 0:
        mock_result.single.return_value = None
    else:
        mock_result.__iter__ = MagicMock(return_value=iter(records))

    mock_session.run.return_value = mock_result
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    return mock_session


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------


class TestKnowledgeGraphClientInit:
    """Tests for client initialization."""

    def test_successful_connection(self) -> None:
        client, mock_driver = _make_client()
        mock_driver.verify_connectivity.assert_called_once()

    def test_connection_failure(self) -> None:
        with patch("keepcontext_ai.graph.neo4j_client.GraphDatabase") as mock_gdb:
            mock_driver = MagicMock()
            mock_driver.verify_connectivity.side_effect = Exception("conn refused")
            mock_gdb.driver.return_value = mock_driver

            with pytest.raises(GraphError, match="Failed to connect"):
                KnowledgeGraphClient(
                    uri="bolt://test:7687",
                    user="neo4j",
                    password="test",
                )

    def test_close(self) -> None:
        client, mock_driver = _make_client()
        client.close()
        mock_driver.close.assert_called_once()


# ---------------------------------------------------------------------------
# store_entity
# ---------------------------------------------------------------------------


class TestStoreEntity:
    """Tests for store_entity method."""

    def test_success(self) -> None:
        client, mock_driver = _make_client()
        _mock_session_run(mock_driver, [{"name": "Auth", "entity_type": "Service"}])

        entity = EntityCreate(name="Auth", entity_type="Service")
        result = client.store_entity(entity)

        assert isinstance(result, Entity)
        assert result.name == "Auth"
        assert result.entity_type == "Service"

    def test_with_properties(self) -> None:
        client, mock_driver = _make_client()
        _mock_session_run(mock_driver, [{"name": "Auth", "entity_type": "Service"}])

        entity = EntityCreate(
            name="Auth",
            entity_type="Service",
            properties={"lang": "python"},
        )
        result = client.store_entity(entity)
        assert result.properties == {"lang": "python"}

    def test_no_record_returned(self) -> None:
        client, mock_driver = _make_client()
        _mock_session_run(mock_driver, [])

        entity = EntityCreate(name="Ghost", entity_type="Unknown")
        with pytest.raises(GraphError, match="Failed to store entity"):
            client.store_entity(entity)

    def test_database_error(self) -> None:
        client, mock_driver = _make_client()
        mock_session = _mock_session_run(mock_driver, [])
        mock_session.run.side_effect = RuntimeError("db down")

        entity = EntityCreate(name="X", entity_type="Y")
        with pytest.raises(GraphError, match="Failed to store entity"):
            client.store_entity(entity)


# ---------------------------------------------------------------------------
# store_relationship
# ---------------------------------------------------------------------------


class TestStoreRelationship:
    """Tests for store_relationship method."""

    def test_success(self) -> None:
        client, mock_driver = _make_client()
        _mock_session_run(mock_driver, [{"source": "A", "target": "B"}])

        rel = RelationshipCreate(
            source="A",
            target="B",
            relationship_type=RelationshipType.USES,
        )
        result = client.store_relationship(rel)

        assert isinstance(result, Relationship)
        assert result.source == "A"
        assert result.target == "B"
        assert result.relationship_type == RelationshipType.USES

    def test_no_record_returned(self) -> None:
        client, mock_driver = _make_client()
        _mock_session_run(mock_driver, [])

        rel = RelationshipCreate(
            source="A",
            target="B",
            relationship_type=RelationshipType.DEPENDS_ON,
        )
        with pytest.raises(GraphError, match="Failed to store relationship"):
            client.store_relationship(rel)


# ---------------------------------------------------------------------------
# get_entity
# ---------------------------------------------------------------------------


class TestGetEntity:
    """Tests for get_entity method."""

    def test_found(self) -> None:
        client, mock_driver = _make_client()
        _mock_session_run(
            mock_driver,
            [
                {
                    "name": "Auth",
                    "entity_type": "Service",
                    "props": {"name": "Auth", "entity_type": "Service"},
                }
            ],
        )

        result = client.get_entity("Auth")
        assert result.name == "Auth"
        assert result.entity_type == "Service"

    def test_not_found(self) -> None:
        client, mock_driver = _make_client()
        _mock_session_run(mock_driver, [])

        with pytest.raises(GraphError, match="Entity not found"):
            client.get_entity("Ghost")


# ---------------------------------------------------------------------------
# query_relationships
# ---------------------------------------------------------------------------


class TestQueryRelationships:
    """Tests for query_relationships method."""

    def test_outgoing_query(self) -> None:
        client, mock_driver = _make_client()
        records = [
            {
                "source_name": "A",
                "target_name": "B",
                "target_type": "Model",
                "rel_type": "USES",
            },
        ]
        # query_relationships iterates over result, so mock __iter__
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter(records))
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__ = MagicMock(
            return_value=mock_session
        )
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

        query = GraphQuery(entity_name="A", direction="outgoing")
        result = client.query_relationships(query)

        assert isinstance(result, GraphResult)
        assert len(result.entities) == 1
        assert len(result.relationships) == 1
        assert result.entities[0].name == "B"

    def test_unknown_rel_type_defaults_to_related(self) -> None:
        client, mock_driver = _make_client()
        records = [
            {
                "source_name": "A",
                "target_name": "B",
                "target_type": "X",
                "rel_type": "UNKNOWN_TYPE",
            },
        ]
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter(records))
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__ = MagicMock(
            return_value=mock_session
        )
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

        query = GraphQuery(entity_name="A", direction="both")
        result = client.query_relationships(query)
        assert result.relationships[0].relationship_type == RelationshipType.RELATED_TO


# ---------------------------------------------------------------------------
# get_dependencies / impact_analysis
# ---------------------------------------------------------------------------


class TestDependenciesAndImpact:
    """Tests for dependency and impact analysis methods."""

    def test_get_dependencies(self) -> None:
        client, mock_driver = _make_client()
        # Returns empty result
        _mock_session_run(mock_driver, [])
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__ = MagicMock(
            return_value=mock_session
        )
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

        result = client.get_dependencies("AuthService")
        assert isinstance(result, GraphResult)

    def test_impact_analysis(self) -> None:
        client, mock_driver = _make_client()
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__ = MagicMock(
            return_value=mock_session
        )
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

        result = client.impact_analysis("AuthService")
        assert isinstance(result, GraphResult)


# ---------------------------------------------------------------------------
# count_entities / clear
# ---------------------------------------------------------------------------


class TestCountAndClear:
    """Tests for count and clear operations."""

    def test_count_entities(self) -> None:
        client, mock_driver = _make_client()
        _mock_session_run(mock_driver, [{"cnt": 42}])

        count = client.count_entities()
        assert count == 42

    def test_count_no_record(self) -> None:
        client, mock_driver = _make_client()
        _mock_session_run(mock_driver, [])

        count = client.count_entities()
        assert count == 0

    def test_clear(self) -> None:
        client, mock_driver = _make_client()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__ = MagicMock(
            return_value=mock_session
        )
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

        client.clear()
        mock_session.run.assert_called_once_with("MATCH (n) DETACH DELETE n")

    def test_clear_failure(self) -> None:
        client, mock_driver = _make_client()
        mock_session = MagicMock()
        mock_session.run.side_effect = RuntimeError("db down")
        mock_driver.session.return_value.__enter__ = MagicMock(
            return_value=mock_session
        )
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(GraphError, match="Failed to clear"):
            client.clear()
