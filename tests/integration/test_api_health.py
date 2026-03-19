"""Integration tests for the /health endpoint."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client: TestClient) -> None:
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "chroma" in data

    def test_health_status_is_healthy(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.json()["status"] == "healthy"

    def test_health_version_matches(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.json()["version"] == "0.1.0-test"

    def test_health_chroma_connected(
        self, client: TestClient, mock_chroma: MagicMock
    ) -> None:
        """When ChromaDB count() succeeds, chroma status should be connected."""
        mock_chroma.count.return_value = 5
        response = client.get("/health")
        assert response.json()["chroma"] == "connected"

    def test_health_chroma_disconnected(
        self, client: TestClient, mock_chroma: MagicMock
    ) -> None:
        """When ChromaDB count() fails, chroma status should be disconnected."""
        mock_chroma.count.side_effect = Exception("connection refused")
        response = client.get("/health")
        assert response.json()["chroma"] == "disconnected"
