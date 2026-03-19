"""Integration tests for /api/v1/context endpoints."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from keepcontext_ai.exceptions import ContextError
from keepcontext_ai.memory.schemas import (
    MemoryEntry,
    MemoryQuery,
    MemoryResult,
    MemoryType,
)

FAKE_TIMESTAMP = "2025-01-01T00:00:00+00:00"


class TestQueryContext:
    """Tests for POST /api/v1/context/query."""

    def test_query_returns_200(
        self, client: TestClient, mock_retriever: MagicMock
    ) -> None:
        mock_retriever.query.return_value = []

        response = client.post(
            "/api/v1/context/query",
            json={"query": "How does auth work?"},
        )

        assert response.status_code == 200

    def test_query_response_has_data_envelope(
        self,
        client: TestClient,
        mock_retriever: MagicMock,
    ) -> None:
        mock_retriever.query.return_value = []

        response = client.post(
            "/api/v1/context/query",
            json={"query": "search"},
        )

        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_query_returns_results(
        self,
        client: TestClient,
        mock_retriever: MagicMock,
    ) -> None:
        entry = MemoryEntry(
            id="uuid-1",
            content="Auth uses JWT tokens",
            memory_type=MemoryType.DECISION,
            created_at=FAKE_TIMESTAMP,
        )
        mock_retriever.query.return_value = [
            MemoryResult(entry=entry, score=0.92),
        ]

        response = client.post(
            "/api/v1/context/query",
            json={"query": "How does authentication work?"},
        )

        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["entry"]["content"] == "Auth uses JWT tokens"
        assert data["data"][0]["score"] == 0.92

    def test_query_with_type_filter(
        self,
        client: TestClient,
        mock_retriever: MagicMock,
    ) -> None:
        mock_retriever.query.return_value = []

        response = client.post(
            "/api/v1/context/query",
            json={"query": "search", "memory_type": "code", "top_k": 3},
        )

        assert response.status_code == 200
        # Verify the MemoryQuery was constructed correctly
        call_args = mock_retriever.query.call_args[0][0]
        assert isinstance(call_args, MemoryQuery)
        assert call_args.memory_type == MemoryType.CODE
        assert call_args.top_k == 3

    def test_query_empty_query_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/context/query",
            json={"query": ""},
        )
        assert response.status_code == 422

    def test_query_missing_body_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/v1/context/query", json={})
        assert response.status_code == 422

    def test_query_context_error_returns_500(
        self,
        client: TestClient,
        mock_retriever: MagicMock,
    ) -> None:
        mock_retriever.query.side_effect = ContextError(
            message="Search failed",
            code="context_search_error",
        )

        response = client.post(
            "/api/v1/context/query",
            json={"query": "search something"},
        )

        assert response.status_code == 500
        assert response.json()["error"]["code"] == "context_search_error"

    def test_query_connection_error_returns_503(
        self,
        client: TestClient,
        mock_retriever: MagicMock,
    ) -> None:
        mock_retriever.query.side_effect = ContextError(
            message="Cannot connect",
            code="memory_connection_error",
        )

        response = client.post(
            "/api/v1/context/query",
            json={"query": "search something"},
        )

        assert response.status_code == 503
