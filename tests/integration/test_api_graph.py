"""Integration tests for graph API routes."""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from keepcontext_ai.exceptions import AppError, GraphError
from keepcontext_ai.graph.schemas import (
    Entity,
    GraphResult,
    Relationship,
    RelationshipType,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_graph() -> MagicMock:
    """Mock KnowledgeGraphClient."""
    from keepcontext_ai.graph.neo4j_client import KnowledgeGraphClient

    mock = MagicMock(spec=KnowledgeGraphClient)
    mock.count_entities.return_value = 0
    return mock


@pytest.fixture()
def graph_app(
    mock_chroma: MagicMock,
    mock_embeddings: MagicMock,
    mock_retriever: MagicMock,
    mock_graph: MagicMock,
) -> FastAPI:
    """FastAPI test app with graph services wired."""
    from keepcontext_ai.api.routes import context, graph, health, memory

    app = FastAPI(title="test-graph")

    app.state.settings = MagicMock()
    app.state.settings.APP_VERSION = "0.1.0-test"
    app.state.settings.APP_NAME = "keepcontext-ai-test"
    app.state.chroma = mock_chroma
    app.state.embeddings = mock_embeddings
    app.state.retriever = mock_retriever
    app.state.graph = mock_graph
    app.state.llm = None

    app.include_router(health.router)
    app.include_router(memory.router)
    app.include_router(context.router)
    app.include_router(graph.router)

    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        status_code = 500
        if exc.code in ("graph_not_found", "memory_not_found"):
            status_code = 404
        elif exc.code == "graph_connection_error":
            status_code = 503
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    return app


@pytest.fixture()
def graph_client(graph_app: FastAPI) -> TestClient:
    """TestClient with graph services."""
    return TestClient(graph_app)


# ---------------------------------------------------------------------------
# POST /api/v1/graph/entities
# ---------------------------------------------------------------------------


class TestCreateEntity:
    """Tests for POST /api/v1/graph/entities."""

    def test_success(self, graph_client: TestClient, mock_graph: MagicMock) -> None:
        mock_graph.store_entity.return_value = Entity(
            name="AuthService", entity_type="Service"
        )

        resp = graph_client.post(
            "/api/v1/graph/entities",
            json={"name": "AuthService", "entity_type": "Service"},
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "AuthService"

    def test_with_properties(
        self, graph_client: TestClient, mock_graph: MagicMock
    ) -> None:
        mock_graph.store_entity.return_value = Entity(
            name="X",
            entity_type="Service",
            properties={"lang": "python"},
        )

        resp = graph_client.post(
            "/api/v1/graph/entities",
            json={
                "name": "X",
                "entity_type": "Service",
                "properties": {"lang": "python"},
            },
        )

        assert resp.status_code == 201

    def test_validation_error(self, graph_client: TestClient) -> None:
        resp = graph_client.post(
            "/api/v1/graph/entities",
            json={"name": "", "entity_type": "Service"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/graph/entities/{name}
# ---------------------------------------------------------------------------


class TestGetEntity:
    """Tests for GET /api/v1/graph/entities/{name}."""

    def test_found(self, graph_client: TestClient, mock_graph: MagicMock) -> None:
        mock_graph.get_entity.return_value = Entity(name="Auth", entity_type="Service")

        resp = graph_client.get("/api/v1/graph/entities/Auth")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Auth"

    def test_not_found(self, graph_client: TestClient, mock_graph: MagicMock) -> None:
        mock_graph.get_entity.side_effect = GraphError(
            message="Entity not found: Ghost",
            code="graph_not_found",
        )

        resp = graph_client.get("/api/v1/graph/entities/Ghost")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/graph/relationships
# ---------------------------------------------------------------------------


class TestCreateRelationship:
    """Tests for POST /api/v1/graph/relationships."""

    def test_success(self, graph_client: TestClient, mock_graph: MagicMock) -> None:
        mock_graph.store_relationship.return_value = Relationship(
            source="A",
            target="B",
            relationship_type=RelationshipType.USES,
        )

        resp = graph_client.post(
            "/api/v1/graph/relationships",
            json={
                "source": "A",
                "target": "B",
                "relationship_type": "USES",
            },
        )

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["source"] == "A"
        assert data["relationship_type"] == "USES"


# ---------------------------------------------------------------------------
# POST /api/v1/graph/query
# ---------------------------------------------------------------------------


class TestQueryGraph:
    """Tests for POST /api/v1/graph/query."""

    def test_success(self, graph_client: TestClient, mock_graph: MagicMock) -> None:
        mock_graph.query_relationships.return_value = GraphResult(
            entities=[Entity(name="B", entity_type="Model")],
            relationships=[
                Relationship(
                    source="A",
                    target="B",
                    relationship_type=RelationshipType.USES,
                )
            ],
        )

        resp = graph_client.post(
            "/api/v1/graph/query",
            json={"entity_name": "A"},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["entities"]) == 1
        assert len(data["relationships"]) == 1

    def test_empty_result(
        self, graph_client: TestClient, mock_graph: MagicMock
    ) -> None:
        mock_graph.query_relationships.return_value = GraphResult()

        resp = graph_client.post(
            "/api/v1/graph/query",
            json={"entity_name": "Unknown"},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["entities"] == []


# ---------------------------------------------------------------------------
# GET /api/v1/graph/dependencies/{name}
# ---------------------------------------------------------------------------


class TestGetDependencies:
    """Tests for GET /api/v1/graph/dependencies/{name}."""

    def test_success(self, graph_client: TestClient, mock_graph: MagicMock) -> None:
        mock_graph.get_dependencies.return_value = GraphResult()

        resp = graph_client.get("/api/v1/graph/dependencies/AuthService")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/v1/graph/impact
# ---------------------------------------------------------------------------


class TestImpactAnalysis:
    """Tests for POST /api/v1/graph/impact."""

    def test_success(self, graph_client: TestClient, mock_graph: MagicMock) -> None:
        mock_graph.impact_analysis.return_value = GraphResult()

        resp = graph_client.post(
            "/api/v1/graph/impact",
            json={"entity_name": "AuthService"},
        )

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/v1/graph/stats
# ---------------------------------------------------------------------------


class TestGraphStats:
    """Tests for GET /api/v1/graph/stats."""

    def test_success(self, graph_client: TestClient, mock_graph: MagicMock) -> None:
        mock_graph.count_entities.return_value = 42

        resp = graph_client.get("/api/v1/graph/stats")
        assert resp.status_code == 200
        assert resp.json()["data"]["entity_count"] == 42
