"""Unit tests for Groq LLM service."""

from unittest.mock import MagicMock, patch

import pytest

from keepcontext_ai.exceptions import LLMError
from keepcontext_ai.graph.schemas import (
    Entity,
    GraphResult,
    Relationship,
    RelationshipType,
)
from keepcontext_ai.memory.schemas import MemoryEntry, MemoryResult, MemoryType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service():
    """Create a GroqLLMService with a mocked Groq client."""
    with patch("keepcontext_ai.llm.groq_service.Groq") as mock_groq_cls:
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client

        from keepcontext_ai.llm.groq_service import GroqLLMService

        service = GroqLLMService(
            api_key="test-key",
            model="test-model",
            max_tokens=1024,
        )
    return service, mock_client


def _mock_completion(mock_client: MagicMock, content: str) -> None:
    """Set up a mock chat completion response."""
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestGroqServiceInit:
    """Tests for GroqLLMService initialization."""

    def test_successful_init(self) -> None:
        service, _ = _make_service()
        assert service._model == "test-model"
        assert service._max_tokens == 1024

    def test_init_failure(self) -> None:
        with patch("keepcontext_ai.llm.groq_service.Groq") as mock_groq_cls:
            mock_groq_cls.side_effect = Exception("bad key")

            from keepcontext_ai.llm.groq_service import GroqLLMService

            with pytest.raises(LLMError, match="Failed to initialize"):
                GroqLLMService(api_key="bad")


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------


class TestGenerate:
    """Tests for the generate method."""

    def test_success(self) -> None:
        service, mock_client = _make_service()
        _mock_completion(mock_client, "Hello world")

        result = service.generate("Say hello")
        assert result == "Hello world"

    def test_empty_prompt_rejected(self) -> None:
        service, _ = _make_service()

        with pytest.raises(LLMError, match="empty prompt"):
            service.generate("")

    def test_whitespace_prompt_rejected(self) -> None:
        service, _ = _make_service()

        with pytest.raises(LLMError, match="empty prompt"):
            service.generate("   ")

    def test_none_content_returns_empty(self) -> None:
        service, mock_client = _make_service()
        _mock_completion(mock_client, None)

        # When content is None, should return ""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        result = service.generate("test")
        assert result == ""

    def test_groq_api_error(self) -> None:
        service, mock_client = _make_service()

        from groq import GroqError

        mock_client.chat.completions.create.side_effect = GroqError("rate limit")

        with pytest.raises(LLMError, match="Groq API request failed"):
            service.generate("test prompt")

    def test_unexpected_error(self) -> None:
        service, mock_client = _make_service()
        mock_client.chat.completions.create.side_effect = RuntimeError("boom")

        with pytest.raises(LLMError, match="Unexpected error"):
            service.generate("test")


# ---------------------------------------------------------------------------
# generate_with_context
# ---------------------------------------------------------------------------


class TestGenerateWithContext:
    """Tests for the generate_with_context method."""

    def test_with_memory_results(self) -> None:
        service, mock_client = _make_service()
        _mock_completion(mock_client, "Auth uses JWT tokens")

        entry = MemoryEntry(
            id="1",
            content="JWT auth",
            memory_type=MemoryType.DECISION,
            created_at="2025-01-01T00:00:00+00:00",
        )
        results = [MemoryResult(entry=entry, score=0.9)]

        response = service.generate_with_context(
            query="How does auth work?",
            memory_results=results,
        )
        assert response == "Auth uses JWT tokens"

    def test_with_graph_result(self) -> None:
        service, mock_client = _make_service()
        _mock_completion(mock_client, "AuthService uses UserModel")

        graph = GraphResult(
            entities=[Entity(name="AuthService", entity_type="Service")],
            relationships=[
                Relationship(
                    source="AuthService",
                    target="UserModel",
                    relationship_type=RelationshipType.USES,
                )
            ],
        )

        response = service.generate_with_context(
            query="What does auth use?",
            graph_result=graph,
        )
        assert response == "AuthService uses UserModel"

    def test_no_context(self) -> None:
        service, mock_client = _make_service()
        _mock_completion(mock_client, "I don't have enough context")

        response = service.generate_with_context(query="Unknown question")
        assert "context" in response.lower()
