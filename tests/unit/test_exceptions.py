"""Unit tests for custom exception hierarchy."""

import pytest

from keepcontext_ai.exceptions import (
    AppError,
    ContextError,
    EmbeddingError,
    MemoryError,
)


class TestAppError:
    """Tests for the base AppError."""

    def test_default_message(self) -> None:
        """AppError should have a default message."""
        err = AppError()
        assert err.message == "An unexpected error occurred"
        assert err.code == "internal_error"

    def test_custom_message_and_code(self) -> None:
        """AppError should accept custom message and code."""
        err = AppError(message="Custom error", code="custom_code")
        assert err.message == "Custom error"
        assert err.code == "custom_code"

    def test_str_representation(self) -> None:
        """str(AppError) should return the message."""
        err = AppError(message="Something went wrong")
        assert str(err) == "Something went wrong"

    def test_is_exception(self) -> None:
        """AppError should be a subclass of Exception."""
        assert issubclass(AppError, Exception)


class TestMemoryError:
    """Tests for MemoryError."""

    def test_default_values(self) -> None:
        err = MemoryError()
        assert err.message == "Memory operation failed"
        assert err.code == "memory_error"

    def test_custom_values(self) -> None:
        err = MemoryError(message="Connection lost", code="memory_connection_error")
        assert err.message == "Connection lost"
        assert err.code == "memory_connection_error"

    def test_inherits_app_error(self) -> None:
        assert issubclass(MemoryError, AppError)

    def test_can_be_caught_as_app_error(self) -> None:
        with pytest.raises(AppError):
            raise MemoryError()


class TestEmbeddingError:
    """Tests for EmbeddingError."""

    def test_default_values(self) -> None:
        err = EmbeddingError()
        assert err.message == "Embedding generation failed"
        assert err.code == "embedding_error"

    def test_custom_values(self) -> None:
        err = EmbeddingError(message="Rate limited", code="embedding_api_error")
        assert err.message == "Rate limited"
        assert err.code == "embedding_api_error"

    def test_inherits_app_error(self) -> None:
        assert issubclass(EmbeddingError, AppError)


class TestContextError:
    """Tests for ContextError."""

    def test_default_values(self) -> None:
        err = ContextError()
        assert err.message == "Context retrieval failed"
        assert err.code == "context_error"

    def test_custom_values(self) -> None:
        err = ContextError(message="Search failed", code="context_search_error")
        assert err.message == "Search failed"
        assert err.code == "context_search_error"

    def test_inherits_app_error(self) -> None:
        assert issubclass(ContextError, AppError)


class TestExceptionChaining:
    """Tests for exception chaining (raise ... from ...)."""

    def test_memory_error_chaining(self) -> None:
        """MemoryError should preserve the original cause."""
        original = ValueError("ChromaDB down")
        try:
            raise MemoryError("Storage failed") from original
        except MemoryError as e:
            assert e.__cause__ is original

    def test_embedding_error_chaining(self) -> None:
        """EmbeddingError should preserve the original cause."""
        original = ConnectionError("API unreachable")
        try:
            raise EmbeddingError("Embedding failed") from original
        except EmbeddingError as e:
            assert e.__cause__ is original
