"""Shared pytest fixtures for all tests.

Provides mock services, test app factory, and reusable test data.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from keepcontext_ai.context import ContextRetriever
from keepcontext_ai.embeddings import EmbeddingService
from keepcontext_ai.memory import ChromaMemoryClient
from keepcontext_ai.memory.schemas import (
    MemoryCreate,
    MemoryEntry,
    MemoryResult,
    MemoryType,
)

# ---------------------------------------------------------------------------
# Reusable test data
# ---------------------------------------------------------------------------

FAKE_EMBEDDING = [0.1] * 128
FAKE_TIMESTAMP = "2025-01-01T00:00:00+00:00"
FAKE_MEMORY_ID = "test-uuid-1234"


@pytest.fixture()
def sample_memory_create() -> MemoryCreate:
    """A valid MemoryCreate instance for tests."""
    return MemoryCreate(
        content="Authentication uses JWT tokens",
        memory_type=MemoryType.DECISION,
        metadata={"author": "test"},
    )


@pytest.fixture()
def sample_memory_entry() -> MemoryEntry:
    """A valid MemoryEntry instance for tests."""
    return MemoryEntry(
        id=FAKE_MEMORY_ID,
        content="Authentication uses JWT tokens",
        memory_type=MemoryType.DECISION,
        metadata={"author": "test"},
        created_at=FAKE_TIMESTAMP,
    )


@pytest.fixture()
def sample_memory_result(sample_memory_entry: MemoryEntry) -> MemoryResult:
    """A valid MemoryResult instance for tests."""
    return MemoryResult(entry=sample_memory_entry, score=0.95)


# ---------------------------------------------------------------------------
# Mock services
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_chroma() -> MagicMock:
    """Mock ChromaMemoryClient."""
    mock = MagicMock(spec=ChromaMemoryClient)
    mock.count.return_value = 0
    return mock


@pytest.fixture()
def mock_embeddings() -> MagicMock:
    """Mock EmbeddingService."""
    mock = MagicMock(spec=EmbeddingService)
    mock.generate.return_value = FAKE_EMBEDDING
    mock.generate_batch.return_value = [FAKE_EMBEDDING]
    return mock


@pytest.fixture()
def mock_retriever() -> MagicMock:
    """Mock ContextRetriever."""
    return MagicMock(spec=ContextRetriever)


# ---------------------------------------------------------------------------
# Test app & client
# ---------------------------------------------------------------------------


def _create_test_app(
    mock_chroma: MagicMock,
    mock_embeddings: MagicMock,
    mock_retriever: MagicMock,
) -> FastAPI:
    """Build a FastAPI app with mocked services wired to app.state."""
    from keepcontext_ai.api.routes import context, health, memory
    from keepcontext_ai.exceptions import AppError

    app = FastAPI(title="test")

    # Wire mock services
    app.state.settings = MagicMock()
    app.state.settings.APP_VERSION = "0.1.0-test"
    app.state.settings.APP_NAME = "keepcontext-ai-test"
    app.state.chroma = mock_chroma
    app.state.embeddings = mock_embeddings
    app.state.retriever = mock_retriever

    # Register routers
    app.include_router(health.router)
    app.include_router(memory.router)
    app.include_router(context.router)

    # Register error handler (mirrors main.py)
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        status_code = 500
        if exc.code in ("memory_not_found", "graph_not_found"):
            status_code = 404
        elif exc.code in (
            "embedding_empty_input",
            "embedding_empty_batch",
            "llm_empty_input",
        ):
            status_code = 422
        elif exc.code in (
            "memory_connection_error",
            "embedding_init_error",
            "graph_connection_error",
            "llm_init_error",
        ):
            status_code = 503
        elif exc.code in ("llm_api_error", "llm_unexpected_error"):
            status_code = 502
        elif exc.code in ("agent_error",):
            status_code = 503
        return JSONResponse(
            status_code=status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    return app


@pytest.fixture()
def test_app(
    mock_chroma: MagicMock,
    mock_embeddings: MagicMock,
    mock_retriever: MagicMock,
) -> FastAPI:
    """FastAPI test app with mocked services."""
    return _create_test_app(mock_chroma, mock_embeddings, mock_retriever)


@pytest.fixture()
def client(test_app: FastAPI) -> TestClient:
    """FastAPI TestClient with mocked services."""
    return TestClient(test_app)
