"""Unit tests for memory schemas and Pydantic models."""

import pytest
from pydantic import ValidationError

from keepcontext_ai.memory.schemas import (
    MemoryCreate,
    MemoryEntry,
    MemoryQuery,
    MemoryResult,
    MemoryType,
    create_timestamp,
)


class TestMemoryType:
    """Tests for the MemoryType enum."""

    def test_all_values_exist(self) -> None:
        assert MemoryType.CONVERSATION == "conversation"
        assert MemoryType.CODE == "code"
        assert MemoryType.DECISION == "decision"
        assert MemoryType.DOCUMENTATION == "documentation"

    def test_is_string_enum(self) -> None:
        assert isinstance(MemoryType.CODE, str)

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError):
            MemoryType("invalid_type")

    def test_count(self) -> None:
        assert len(MemoryType) == 4


class TestMemoryCreate:
    """Tests for the MemoryCreate model."""

    def test_valid_creation(self) -> None:
        entry = MemoryCreate(content="Test content", memory_type=MemoryType.CODE)
        assert entry.content == "Test content"
        assert entry.memory_type == MemoryType.CODE
        assert entry.metadata == {}

    def test_default_memory_type(self) -> None:
        entry = MemoryCreate(content="Some text")
        assert entry.memory_type == MemoryType.DOCUMENTATION

    def test_with_metadata(self) -> None:
        entry = MemoryCreate(
            content="Auth decision",
            memory_type=MemoryType.DECISION,
            metadata={"author": "alice", "sprint": "3"},
        )
        assert entry.metadata == {"author": "alice", "sprint": "3"}

    def test_empty_content_raises(self) -> None:
        with pytest.raises(ValidationError):
            MemoryCreate(content="")

    def test_content_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            MemoryCreate(content="x" * 50001)

    def test_is_frozen(self) -> None:
        entry = MemoryCreate(content="Test")
        with pytest.raises(ValidationError):
            entry.content = "Changed"  # type: ignore[misc]


class TestMemoryEntry:
    """Tests for the MemoryEntry model."""

    def test_valid_creation(self) -> None:
        entry = MemoryEntry(
            id="uuid-123",
            content="Test",
            memory_type=MemoryType.CODE,
            created_at="2025-01-01T00:00:00+00:00",
        )
        assert entry.id == "uuid-123"
        assert entry.content == "Test"
        assert entry.memory_type == MemoryType.CODE
        assert entry.metadata == {}
        assert entry.created_at == "2025-01-01T00:00:00+00:00"

    def test_missing_required_fields_raises(self) -> None:
        with pytest.raises(ValidationError):
            MemoryEntry(content="Test")  # type: ignore[call-arg]

    def test_is_frozen(self) -> None:
        entry = MemoryEntry(
            id="uuid-123",
            content="Test",
            memory_type=MemoryType.CODE,
            created_at="2025-01-01T00:00:00+00:00",
        )
        with pytest.raises(ValidationError):
            entry.id = "changed"  # type: ignore[misc]

    def test_model_dump(self) -> None:
        entry = MemoryEntry(
            id="uuid-123",
            content="Test",
            memory_type=MemoryType.CODE,
            metadata={"key": "val"},
            created_at="2025-01-01T00:00:00+00:00",
        )
        data = entry.model_dump()
        assert data["id"] == "uuid-123"
        assert data["memory_type"] == "code"
        assert data["metadata"] == {"key": "val"}


class TestMemoryQuery:
    """Tests for the MemoryQuery model."""

    def test_valid_query(self) -> None:
        query = MemoryQuery(query="How does auth work?")
        assert query.query == "How does auth work?"
        assert query.top_k == 5
        assert query.memory_type is None

    def test_with_type_filter(self) -> None:
        query = MemoryQuery(query="search", memory_type=MemoryType.DECISION)
        assert query.memory_type == MemoryType.DECISION

    def test_custom_top_k(self) -> None:
        query = MemoryQuery(query="search", top_k=10)
        assert query.top_k == 10

    def test_top_k_too_low_raises(self) -> None:
        with pytest.raises(ValidationError):
            MemoryQuery(query="search", top_k=0)

    def test_top_k_too_high_raises(self) -> None:
        with pytest.raises(ValidationError):
            MemoryQuery(query="search", top_k=51)

    def test_empty_query_raises(self) -> None:
        with pytest.raises(ValidationError):
            MemoryQuery(query="")

    def test_query_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            MemoryQuery(query="x" * 5001)

    def test_is_frozen(self) -> None:
        query = MemoryQuery(query="search")
        with pytest.raises(ValidationError):
            query.query = "changed"  # type: ignore[misc]


class TestMemoryResult:
    """Tests for the MemoryResult model."""

    def test_valid_result(self) -> None:
        entry = MemoryEntry(
            id="uuid-123",
            content="Test",
            memory_type=MemoryType.CODE,
            created_at="2025-01-01T00:00:00+00:00",
        )
        result = MemoryResult(entry=entry, score=0.85)
        assert result.entry.id == "uuid-123"
        assert result.score == 0.85

    def test_score_too_low_raises(self) -> None:
        entry = MemoryEntry(
            id="uuid-123",
            content="Test",
            memory_type=MemoryType.CODE,
            created_at="2025-01-01T00:00:00+00:00",
        )
        with pytest.raises(ValidationError):
            MemoryResult(entry=entry, score=-0.1)

    def test_score_too_high_raises(self) -> None:
        entry = MemoryEntry(
            id="uuid-123",
            content="Test",
            memory_type=MemoryType.CODE,
            created_at="2025-01-01T00:00:00+00:00",
        )
        with pytest.raises(ValidationError):
            MemoryResult(entry=entry, score=1.1)

    def test_is_frozen(self) -> None:
        entry = MemoryEntry(
            id="uuid-123",
            content="Test",
            memory_type=MemoryType.CODE,
            created_at="2025-01-01T00:00:00+00:00",
        )
        result = MemoryResult(entry=entry, score=0.5)
        with pytest.raises(ValidationError):
            result.score = 0.9  # type: ignore[misc]


class TestCreateTimestamp:
    """Tests for the create_timestamp helper."""

    def test_returns_string(self) -> None:
        ts = create_timestamp()
        assert isinstance(ts, str)

    def test_is_iso_format(self) -> None:
        ts = create_timestamp()
        # Should contain timezone info (UTC offset)
        assert "+" in ts or "Z" in ts

    def test_contains_date_and_time(self) -> None:
        ts = create_timestamp()
        assert "T" in ts  # ISO 8601 separator
