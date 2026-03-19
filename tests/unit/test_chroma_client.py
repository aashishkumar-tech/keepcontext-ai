"""Unit tests for ChromaMemoryClient."""

from unittest.mock import MagicMock, patch

import pytest

from keepcontext_ai.exceptions import MemoryError
from keepcontext_ai.memory.chroma_client import ChromaMemoryClient
from keepcontext_ai.memory.schemas import (
    MemoryCreate,
    MemoryEntry,
    MemoryResult,
    MemoryType,
)

FAKE_EMBEDDING = [0.1] * 128


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client() -> ChromaMemoryClient:
    """Create a ChromaMemoryClient with a mocked ChromaDB backend."""
    with patch("keepcontext_ai.memory.chroma_client.chromadb") as mock_chromadb:
        mock_collection = MagicMock()
        mock_http_client = MagicMock()
        mock_http_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.HttpClient.return_value = mock_http_client

        client = ChromaMemoryClient(host="localhost", port=8100)
        # Expose mock for assertions
        client._mock_collection = mock_collection  # type: ignore[attr-defined]
        return client


def _chroma_get_result(
    memory_id: str = "uuid-1",
    content: str = "Test content",
    memory_type: str = "code",
    created_at: str = "2025-01-01T00:00:00+00:00",
) -> dict:
    """Build a fake ChromaDB get result."""
    return {
        "ids": [memory_id],
        "documents": [content],
        "metadatas": [
            {
                "memory_type": memory_type,
                "created_at": created_at,
            }
        ],
    }


def _chroma_query_result(
    memory_id: str = "uuid-1",
    content: str = "Test content",
    memory_type: str = "code",
    distance: float = 0.2,
) -> dict:
    """Build a fake ChromaDB query result."""
    return {
        "ids": [[memory_id]],
        "documents": [[content]],
        "metadatas": [
            [{"memory_type": memory_type, "created_at": "2025-01-01T00:00:00+00:00"}]
        ],
        "distances": [[distance]],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestChromaClientInit:
    """Tests for ChromaMemoryClient initialization."""

    def test_init_success(self) -> None:
        client = _make_client()
        assert client._collection is not None

    def test_init_connection_failure_raises_memory_error(self) -> None:
        with patch("keepcontext_ai.memory.chroma_client.chromadb") as mock_chromadb:
            mock_chromadb.HttpClient.side_effect = ConnectionError("refused")
            with pytest.raises(MemoryError) as exc_info:
                ChromaMemoryClient(host="bad-host", port=9999)
            assert exc_info.value.code == "memory_connection_error"


class TestChromaClientStore:
    """Tests for the store() method."""

    def test_store_returns_memory_entry(self) -> None:
        client = _make_client()
        entry = MemoryCreate(content="Auth uses JWT", memory_type=MemoryType.DECISION)

        result = client.store(entry, FAKE_EMBEDDING)

        assert isinstance(result, MemoryEntry)
        assert result.content == "Auth uses JWT"
        assert result.memory_type == MemoryType.DECISION
        assert result.id  # UUID generated
        assert result.created_at  # Timestamp generated

    def test_store_calls_collection_add(self) -> None:
        client = _make_client()
        entry = MemoryCreate(content="Test", memory_type=MemoryType.CODE)

        client.store(entry, FAKE_EMBEDDING)

        client._mock_collection.add.assert_called_once()  # type: ignore[attr-defined]
        call_kwargs = client._mock_collection.add.call_args  # type: ignore[attr-defined]
        assert call_kwargs[1]["documents"] == ["Test"]

    def test_store_failure_raises_memory_error(self) -> None:
        client = _make_client()
        client._mock_collection.add.side_effect = Exception("disk full")  # type: ignore[attr-defined]
        entry = MemoryCreate(content="Test", memory_type=MemoryType.CODE)

        with pytest.raises(MemoryError) as exc_info:
            client.store(entry, FAKE_EMBEDDING)
        assert exc_info.value.code == "memory_store_error"


class TestChromaClientGet:
    """Tests for the get() method."""

    def test_get_returns_entry(self) -> None:
        client = _make_client()
        client._mock_collection.get.return_value = _chroma_get_result()  # type: ignore[attr-defined]

        entry = client.get("uuid-1")

        assert isinstance(entry, MemoryEntry)
        assert entry.id == "uuid-1"
        assert entry.content == "Test content"

    def test_get_not_found_raises_memory_error(self) -> None:
        client = _make_client()
        client._mock_collection.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }  # type: ignore[attr-defined]

        with pytest.raises(MemoryError) as exc_info:
            client.get("nonexistent")
        assert exc_info.value.code == "memory_not_found"

    def test_get_failure_raises_memory_error(self) -> None:
        client = _make_client()
        client._mock_collection.get.side_effect = Exception("timeout")  # type: ignore[attr-defined]

        with pytest.raises(MemoryError) as exc_info:
            client.get("uuid-1")
        assert exc_info.value.code == "memory_get_error"


class TestChromaClientListEntries:
    """Tests for the list_entries() method."""

    def test_list_returns_entries(self) -> None:
        client = _make_client()
        client._mock_collection.get.return_value = _chroma_get_result()  # type: ignore[attr-defined]

        entries = client.list_entries(limit=10, offset=0)

        assert len(entries) == 1
        assert entries[0].id == "uuid-1"

    def test_list_with_type_filter(self) -> None:
        client = _make_client()
        client._mock_collection.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }  # type: ignore[attr-defined]

        entries = client.list_entries(memory_type=MemoryType.CODE)

        assert entries == []
        call_kwargs = client._mock_collection.get.call_args[1]  # type: ignore[attr-defined]
        assert call_kwargs["where"] == {"memory_type": "code"}

    def test_list_empty_result(self) -> None:
        client = _make_client()
        client._mock_collection.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }  # type: ignore[attr-defined]

        entries = client.list_entries()

        assert entries == []

    def test_list_failure_raises_memory_error(self) -> None:
        client = _make_client()
        client._mock_collection.get.side_effect = Exception("error")  # type: ignore[attr-defined]

        with pytest.raises(MemoryError) as exc_info:
            client.list_entries()
        assert exc_info.value.code == "memory_list_error"


class TestChromaClientDelete:
    """Tests for the delete() method."""

    def test_delete_calls_collection(self) -> None:
        client = _make_client()
        # get() is called first to verify existence
        client._mock_collection.get.return_value = _chroma_get_result()  # type: ignore[attr-defined]

        client.delete("uuid-1")

        client._mock_collection.delete.assert_called_once_with(ids=["uuid-1"])  # type: ignore[attr-defined]

    def test_delete_not_found_raises(self) -> None:
        client = _make_client()
        client._mock_collection.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }  # type: ignore[attr-defined]

        with pytest.raises(MemoryError) as exc_info:
            client.delete("nonexistent")
        assert exc_info.value.code == "memory_not_found"

    def test_delete_failure_raises_memory_error(self) -> None:
        client = _make_client()
        client._mock_collection.get.return_value = _chroma_get_result()  # type: ignore[attr-defined]
        client._mock_collection.delete.side_effect = Exception("error")  # type: ignore[attr-defined]

        with pytest.raises(MemoryError) as exc_info:
            client.delete("uuid-1")
        assert exc_info.value.code == "memory_delete_error"


class TestChromaClientQuery:
    """Tests for the query() method."""

    def test_query_returns_results(self) -> None:
        client = _make_client()
        client._mock_collection.query.return_value = _chroma_query_result()  # type: ignore[attr-defined]

        results = client.query(FAKE_EMBEDDING, top_k=5)

        assert len(results) == 1
        assert isinstance(results[0], MemoryResult)
        assert results[0].entry.id == "uuid-1"
        assert results[0].score == pytest.approx(0.8)  # 1.0 - 0.2

    def test_query_with_type_filter(self) -> None:
        client = _make_client()
        client._mock_collection.query.return_value = _chroma_query_result()  # type: ignore[attr-defined]

        client.query(FAKE_EMBEDDING, memory_type=MemoryType.DECISION)

        call_kwargs = client._mock_collection.query.call_args[1]  # type: ignore[attr-defined]
        assert call_kwargs["where"] == {"memory_type": "decision"}

    def test_query_empty_results(self) -> None:
        client = _make_client()
        client._mock_collection.query.return_value = {  # type: ignore[attr-defined]
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        results = client.query(FAKE_EMBEDDING)

        assert results == []

    def test_query_failure_raises_memory_error(self) -> None:
        client = _make_client()
        client._mock_collection.query.side_effect = Exception("error")  # type: ignore[attr-defined]

        with pytest.raises(MemoryError) as exc_info:
            client.query(FAKE_EMBEDDING)
        assert exc_info.value.code == "memory_query_error"

    def test_query_score_clamped_to_0_1(self) -> None:
        """Score should be clamped between 0 and 1."""
        client = _make_client()
        client._mock_collection.query.return_value = _chroma_query_result(distance=2.0)  # type: ignore[attr-defined]

        results = client.query(FAKE_EMBEDDING)

        # 1.0 - 2.0 = -1.0, clamped to 0.0
        assert results[0].score == 0.0


class TestChromaClientCount:
    """Tests for the count() method."""

    def test_count_returns_int(self) -> None:
        client = _make_client()
        client._mock_collection.count.return_value = 42  # type: ignore[attr-defined]

        assert client.count() == 42

    def test_count_failure_raises_memory_error(self) -> None:
        client = _make_client()
        client._mock_collection.count.side_effect = Exception("error")  # type: ignore[attr-defined]

        with pytest.raises(MemoryError) as exc_info:
            client.count()
        assert exc_info.value.code == "memory_count_error"
