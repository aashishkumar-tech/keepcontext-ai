"""Integration tests for /api/v1/memory endpoints."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from keepcontext_ai.exceptions import MemoryError
from keepcontext_ai.memory.schemas import MemoryEntry, MemoryType

FAKE_TIMESTAMP = "2025-01-01T00:00:00+00:00"
FAKE_EMBEDDING = [0.1] * 128


class TestStoreMemory:
    """Tests for POST /api/v1/memory."""

    def test_store_returns_201(
        self,
        client: TestClient,
        mock_chroma: MagicMock,
        mock_embeddings: MagicMock,
    ) -> None:
        mock_embeddings.generate.return_value = FAKE_EMBEDDING
        mock_chroma.store.return_value = MemoryEntry(
            id="uuid-new",
            content="Test content",
            memory_type=MemoryType.CODE,
            created_at=FAKE_TIMESTAMP,
        )

        response = client.post(
            "/api/v1/memory",
            json={"content": "Test content", "memory_type": "code"},
        )

        assert response.status_code == 201

    def test_store_response_has_data_envelope(
        self,
        client: TestClient,
        mock_chroma: MagicMock,
        mock_embeddings: MagicMock,
    ) -> None:
        mock_embeddings.generate.return_value = FAKE_EMBEDDING
        mock_chroma.store.return_value = MemoryEntry(
            id="uuid-new",
            content="Auth uses JWT",
            memory_type=MemoryType.DECISION,
            metadata={"author": "test"},
            created_at=FAKE_TIMESTAMP,
        )

        response = client.post(
            "/api/v1/memory",
            json={
                "content": "Auth uses JWT",
                "memory_type": "decision",
                "metadata": {"author": "test"},
            },
        )

        data = response.json()
        assert "data" in data
        assert data["data"]["id"] == "uuid-new"
        assert data["data"]["content"] == "Auth uses JWT"
        assert data["data"]["memory_type"] == "decision"

    def test_store_empty_content_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/memory",
            json={"content": ""},
        )
        assert response.status_code == 422

    def test_store_missing_content_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/v1/memory", json={})
        assert response.status_code == 422

    def test_store_embedding_failure_returns_error(
        self,
        client: TestClient,
        mock_embeddings: MagicMock,
    ) -> None:
        from keepcontext_ai.exceptions import EmbeddingError

        mock_embeddings.generate.side_effect = EmbeddingError(
            message="Empty input", code="embedding_empty_input"
        )

        response = client.post(
            "/api/v1/memory",
            json={"content": "Test"},
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "embedding_empty_input"


class TestListMemories:
    """Tests for GET /api/v1/memory."""

    def test_list_returns_200(self, client: TestClient, mock_chroma: MagicMock) -> None:
        mock_chroma.list_entries.return_value = []
        mock_chroma.count.return_value = 0

        response = client.get("/api/v1/memory")
        assert response.status_code == 200

    def test_list_response_structure(
        self, client: TestClient, mock_chroma: MagicMock
    ) -> None:
        mock_chroma.list_entries.return_value = []
        mock_chroma.count.return_value = 0

        response = client.get("/api/v1/memory")
        data = response.json()

        assert "data" in data
        assert "meta" in data
        assert data["meta"]["total"] == 0
        assert data["meta"]["limit"] == 20
        assert data["meta"]["offset"] == 0

    def test_list_with_entries(
        self, client: TestClient, mock_chroma: MagicMock
    ) -> None:
        mock_chroma.list_entries.return_value = [
            MemoryEntry(
                id="uuid-1",
                content="Entry 1",
                memory_type=MemoryType.CODE,
                created_at=FAKE_TIMESTAMP,
            ),
        ]
        mock_chroma.count.return_value = 1

        response = client.get("/api/v1/memory")
        data = response.json()

        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "uuid-1"
        assert data["meta"]["total"] == 1

    def test_list_with_pagination_params(
        self, client: TestClient, mock_chroma: MagicMock
    ) -> None:
        mock_chroma.list_entries.return_value = []
        mock_chroma.count.return_value = 50

        response = client.get("/api/v1/memory?limit=10&offset=20")
        data = response.json()

        assert data["meta"]["limit"] == 10
        assert data["meta"]["offset"] == 20
        mock_chroma.list_entries.assert_called_once_with(
            limit=10,
            offset=20,
            memory_type=None,
        )

    def test_list_with_type_filter(
        self, client: TestClient, mock_chroma: MagicMock
    ) -> None:
        mock_chroma.list_entries.return_value = []
        mock_chroma.count.return_value = 0

        response = client.get("/api/v1/memory?memory_type=decision")

        assert response.status_code == 200
        mock_chroma.list_entries.assert_called_once_with(
            limit=20,
            offset=0,
            memory_type=MemoryType.DECISION,
        )


class TestGetMemory:
    """Tests for GET /api/v1/memory/{id}."""

    def test_get_returns_200(self, client: TestClient, mock_chroma: MagicMock) -> None:
        mock_chroma.get.return_value = MemoryEntry(
            id="uuid-1",
            content="Test",
            memory_type=MemoryType.CODE,
            created_at=FAKE_TIMESTAMP,
        )

        response = client.get("/api/v1/memory/uuid-1")
        assert response.status_code == 200

    def test_get_response_envelope(
        self, client: TestClient, mock_chroma: MagicMock
    ) -> None:
        mock_chroma.get.return_value = MemoryEntry(
            id="uuid-1",
            content="Test",
            memory_type=MemoryType.CODE,
            created_at=FAKE_TIMESTAMP,
        )

        response = client.get("/api/v1/memory/uuid-1")
        data = response.json()

        assert "data" in data
        assert data["data"]["id"] == "uuid-1"

    def test_get_not_found_returns_404(
        self, client: TestClient, mock_chroma: MagicMock
    ) -> None:
        mock_chroma.get.side_effect = MemoryError(
            message="Memory entry not found: nonexistent",
            code="memory_not_found",
        )

        response = client.get("/api/v1/memory/nonexistent")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "memory_not_found"


class TestDeleteMemory:
    """Tests for DELETE /api/v1/memory/{id}."""

    def test_delete_returns_204(
        self, client: TestClient, mock_chroma: MagicMock
    ) -> None:
        mock_chroma.delete.return_value = None

        response = client.delete("/api/v1/memory/uuid-1")
        assert response.status_code == 204

    def test_delete_empty_body(
        self, client: TestClient, mock_chroma: MagicMock
    ) -> None:
        mock_chroma.delete.return_value = None

        response = client.delete("/api/v1/memory/uuid-1")
        assert response.content == b""

    def test_delete_not_found_returns_404(
        self, client: TestClient, mock_chroma: MagicMock
    ) -> None:
        mock_chroma.delete.side_effect = MemoryError(
            message="Memory entry not found: nonexistent",
            code="memory_not_found",
        )

        response = client.delete("/api/v1/memory/nonexistent")
        assert response.status_code == 404
