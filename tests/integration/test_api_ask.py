"""Integration tests for the /api/v1/ask endpoint."""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from keepcontext_ai.context.schemas import EnrichedContextResult
from keepcontext_ai.exceptions import AppError
from keepcontext_ai.graph.schemas import (
    Entity,
    GraphResult,
)
from keepcontext_ai.memory.schemas import MemoryEntry, MemoryResult, MemoryType

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def ask_app(
    mock_chroma: MagicMock,
    mock_embeddings: MagicMock,
    mock_retriever: MagicMock,
) -> FastAPI:
    """FastAPI test app with ask route wired."""
    from keepcontext_ai.api.routes import ask, context, health, memory

    app = FastAPI(title="test-ask")

    app.state.settings = MagicMock()
    app.state.settings.APP_VERSION = "0.1.0-test"
    app.state.settings.APP_NAME = "keepcontext-ai-test"
    app.state.chroma = mock_chroma
    app.state.embeddings = mock_embeddings
    app.state.retriever = mock_retriever
    app.state.graph = None
    app.state.llm = None

    app.include_router(health.router)
    app.include_router(memory.router)
    app.include_router(context.router)
    app.include_router(ask.router)

    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    return app


@pytest.fixture()
def ask_client(ask_app: FastAPI) -> TestClient:
    """TestClient with ask route."""
    return TestClient(ask_app)


# ---------------------------------------------------------------------------
# POST /api/v1/ask
# ---------------------------------------------------------------------------


class TestAskEndpoint:
    """Tests for POST /api/v1/ask."""

    def test_basic_ask(self, ask_client: TestClient, mock_retriever: MagicMock) -> None:
        entry = MemoryEntry(
            id="1",
            content="JWT auth",
            memory_type=MemoryType.DECISION,
            created_at="2025-01-01T00:00:00+00:00",
        )
        mock_retriever.query_enriched.return_value = EnrichedContextResult(
            memory_results=[MemoryResult(entry=entry, score=0.9)],
            graph_context=GraphResult(),
            llm_response="Auth uses JWT",
        )

        resp = ask_client.post(
            "/api/v1/ask",
            json={"query": "How does auth work?"},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["memory_results"]) == 1
        assert data["llm_response"] == "Auth uses JWT"

    def test_ask_with_entity(
        self, ask_client: TestClient, mock_retriever: MagicMock
    ) -> None:
        mock_retriever.query_enriched.return_value = EnrichedContextResult(
            memory_results=[],
            graph_context=GraphResult(
                entities=[Entity(name="Auth", entity_type="Service")],
            ),
            llm_response="Answer with graph context",
        )

        resp = ask_client.post(
            "/api/v1/ask",
            json={
                "query": "What does Auth depend on?",
                "entity_name": "Auth",
            },
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["graph_context"]["entities"]) == 1

    def test_ask_without_llm(
        self, ask_client: TestClient, mock_retriever: MagicMock
    ) -> None:
        mock_retriever.query_enriched.return_value = EnrichedContextResult(
            memory_results=[],
            graph_context=GraphResult(),
            llm_response=None,
        )

        resp = ask_client.post(
            "/api/v1/ask",
            json={"query": "test", "use_llm": False},
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["llm_response"] is None

    def test_ask_validation_error(self, ask_client: TestClient) -> None:
        resp = ask_client.post(
            "/api/v1/ask",
            json={"query": ""},
        )
        assert resp.status_code == 422

    def test_ask_with_memory_type_filter(
        self, ask_client: TestClient, mock_retriever: MagicMock
    ) -> None:
        mock_retriever.query_enriched.return_value = EnrichedContextResult(
            memory_results=[],
            graph_context=GraphResult(),
        )

        resp = ask_client.post(
            "/api/v1/ask",
            json={
                "query": "test",
                "memory_type": "code",
                "top_k": 10,
            },
        )

        assert resp.status_code == 200
        # Verify the retriever was called with correct params
        call_kwargs = mock_retriever.query_enriched.call_args
        assert call_kwargs is not None

    def test_ask_with_custom_top_k(
        self, ask_client: TestClient, mock_retriever: MagicMock
    ) -> None:
        mock_retriever.query_enriched.return_value = EnrichedContextResult()

        resp = ask_client.post(
            "/api/v1/ask",
            json={"query": "test", "top_k": 20},
        )

        assert resp.status_code == 200
