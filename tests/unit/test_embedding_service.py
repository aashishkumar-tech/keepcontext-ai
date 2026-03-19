"""Unit tests for EmbeddingService."""

from unittest.mock import MagicMock, patch

import pytest

from keepcontext_ai.embeddings.embedding_service import EmbeddingService
from keepcontext_ai.exceptions import EmbeddingError

FAKE_EMBEDDING = [0.1] * 128


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service() -> EmbeddingService:
    """Create an EmbeddingService with a mocked OpenAI client."""
    with patch("keepcontext_ai.embeddings.embedding_service.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        service = EmbeddingService(api_key="sk-test", model="text-embedding-3-small")
        service._mock_client = mock_client  # type: ignore[attr-defined]
        return service


def _mock_embedding_response(embedding: list[float]) -> MagicMock:
    """Build a mock OpenAI embedding response."""
    mock_data = MagicMock()
    mock_data.embedding = embedding
    mock_data.index = 0

    mock_response = MagicMock()
    mock_response.data = [mock_data]
    return mock_response


def _mock_batch_response(embeddings: list[list[float]]) -> MagicMock:
    """Build a mock OpenAI batch embedding response."""
    mock_items = []
    for i, emb in enumerate(embeddings):
        item = MagicMock()
        item.embedding = emb
        item.index = i
        mock_items.append(item)

    mock_response = MagicMock()
    mock_response.data = mock_items
    return mock_response


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEmbeddingServiceInit:
    """Tests for EmbeddingService initialization."""

    def test_init_success(self) -> None:
        service = _make_service()
        assert service._model == "text-embedding-3-small"

    def test_init_failure_raises_embedding_error(self) -> None:
        with patch("keepcontext_ai.embeddings.embedding_service.OpenAI") as mock_openai:
            mock_openai.side_effect = Exception("invalid key")
            with pytest.raises(EmbeddingError) as exc_info:
                EmbeddingService(api_key="bad-key")
            assert exc_info.value.code == "embedding_init_error"


class TestEmbeddingServiceGenerate:
    """Tests for the generate() method."""

    def test_generate_returns_embedding(self) -> None:
        service = _make_service()
        service._mock_client.embeddings.create.return_value = _mock_embedding_response(
            FAKE_EMBEDDING
        )  # type: ignore[attr-defined]

        result = service.generate("Hello world")

        assert result == FAKE_EMBEDDING

    def test_generate_calls_openai_with_correct_params(self) -> None:
        service = _make_service()
        service._mock_client.embeddings.create.return_value = _mock_embedding_response(
            FAKE_EMBEDDING
        )  # type: ignore[attr-defined]

        service.generate("Test text")

        service._mock_client.embeddings.create.assert_called_once_with(  # type: ignore[attr-defined]
            input="Test text",
            model="text-embedding-3-small",
        )

    def test_generate_empty_text_raises(self) -> None:
        service = _make_service()

        with pytest.raises(EmbeddingError) as exc_info:
            service.generate("")
        assert exc_info.value.code == "embedding_empty_input"

    def test_generate_whitespace_only_raises(self) -> None:
        service = _make_service()

        with pytest.raises(EmbeddingError) as exc_info:
            service.generate("   ")
        assert exc_info.value.code == "embedding_empty_input"

    def test_generate_openai_error_raises(self) -> None:
        from openai import OpenAIError

        service = _make_service()
        service._mock_client.embeddings.create.side_effect = OpenAIError("rate limit")  # type: ignore[attr-defined]

        with pytest.raises(EmbeddingError) as exc_info:
            service.generate("Test")
        assert exc_info.value.code == "embedding_api_error"

    def test_generate_unexpected_error_raises(self) -> None:
        service = _make_service()
        service._mock_client.embeddings.create.side_effect = RuntimeError("unknown")  # type: ignore[attr-defined]

        with pytest.raises(EmbeddingError) as exc_info:
            service.generate("Test")
        assert exc_info.value.code == "embedding_unexpected_error"


class TestEmbeddingServiceGenerateBatch:
    """Tests for the generate_batch() method."""

    def test_batch_returns_embeddings(self) -> None:
        service = _make_service()
        batch_embeddings = [FAKE_EMBEDDING, FAKE_EMBEDDING]
        service._mock_client.embeddings.create.return_value = _mock_batch_response(
            batch_embeddings
        )  # type: ignore[attr-defined]

        result = service.generate_batch(["Text 1", "Text 2"])

        assert len(result) == 2
        assert result[0] == FAKE_EMBEDDING

    def test_batch_empty_list_raises(self) -> None:
        service = _make_service()

        with pytest.raises(EmbeddingError) as exc_info:
            service.generate_batch([])
        assert exc_info.value.code == "embedding_empty_batch"

    def test_batch_with_empty_text_raises(self) -> None:
        service = _make_service()

        with pytest.raises(EmbeddingError) as exc_info:
            service.generate_batch(["Valid", ""])
        assert exc_info.value.code == "embedding_empty_input"

    def test_batch_openai_error_raises(self) -> None:
        from openai import OpenAIError

        service = _make_service()
        service._mock_client.embeddings.create.side_effect = OpenAIError("quota")  # type: ignore[attr-defined]

        with pytest.raises(EmbeddingError) as exc_info:
            service.generate_batch(["Test"])
        assert exc_info.value.code == "embedding_api_error"
