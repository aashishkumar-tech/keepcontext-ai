"""Unit tests for application configuration."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from keepcontext_ai.config import Settings, get_settings

# ---------------------------------------------------------------------------
# Required env vars for a valid Settings instance
# ---------------------------------------------------------------------------

VALID_ENV = {
    "OPENAI_API_KEY": "sk-test-key-123",
    "GROQ_API_KEY": "gsk-test-key-456",
    "NEO4J_USER": "neo4j",
    "NEO4J_PASSWORD": "test-password",
}


def _make_settings(**overrides: str) -> Settings:
    """Create Settings with _env_file=None to ignore .env on disk."""
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


class TestSettings:
    """Tests for the Settings model."""

    @patch.dict(os.environ, VALID_ENV, clear=False)
    def test_settings_loads_with_required_keys(self) -> None:
        """Settings should load when required API keys are present."""
        settings = _make_settings()
        assert settings.OPENAI_API_KEY == "sk-test-key-123"
        assert settings.GROQ_API_KEY == "gsk-test-key-456"

    @patch.dict(os.environ, VALID_ENV, clear=False)
    def test_settings_default_values(self) -> None:
        """Settings should have correct defaults for optional fields."""
        settings = _make_settings()
        assert settings.APP_NAME == "keepcontext-ai"
        assert settings.APP_VERSION == "0.1.0"
        assert settings.DEBUG is False
        assert settings.LOG_LEVEL == "INFO"
        assert settings.CHROMA_HOST == "localhost"
        assert settings.CHROMA_PORT == 8100
        assert settings.OPENAI_EMBEDDING_MODEL == "text-embedding-3-small"

    @patch.dict(
        os.environ, {**VALID_ENV, "DEBUG": "true", "LOG_LEVEL": "DEBUG"}, clear=False
    )
    def test_settings_overrides_from_env(self) -> None:
        """Settings should pick up overrides from environment variables."""
        settings = _make_settings()
        assert settings.DEBUG is True
        assert settings.LOG_LEVEL == "DEBUG"

    def test_settings_missing_openai_key_raises(self) -> None:
        """Settings should raise ValidationError if OPENAI_API_KEY is missing."""
        env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
        env["GROQ_API_KEY"] = "gsk-test"
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError):
                _make_settings()

    def test_settings_missing_groq_key_raises(self) -> None:
        """Settings should raise ValidationError if GROQ_API_KEY is missing."""
        env = {k: v for k, v in os.environ.items() if k != "GROQ_API_KEY"}
        env["OPENAI_API_KEY"] = "sk-test"
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError):
                _make_settings()

    @patch.dict(os.environ, VALID_ENV, clear=False)
    def test_settings_is_frozen(self) -> None:
        """Settings should be immutable (frozen)."""
        settings = _make_settings()
        with pytest.raises(ValidationError):
            settings.APP_NAME = "changed"  # type: ignore[misc]

    @patch.dict(os.environ, VALID_ENV, clear=False)
    def test_settings_chroma_port_is_int(self) -> None:
        """CHROMA_PORT should be coerced to int."""
        settings = _make_settings()
        assert isinstance(settings.CHROMA_PORT, int)


class TestGetSettings:
    """Tests for the get_settings() factory function."""

    @patch.dict(os.environ, VALID_ENV, clear=False)
    def test_get_settings_returns_settings_instance(self) -> None:
        """get_settings() should return a valid Settings object."""
        settings = get_settings()
        assert isinstance(settings, Settings)
        assert settings.OPENAI_API_KEY == "sk-test-key-123"
