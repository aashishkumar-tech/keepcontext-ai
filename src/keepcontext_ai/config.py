"""Application configuration.

Uses Pydantic BaseSettings for type-safe, validated configuration
loaded from environment variables and .env files.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment variables.

    Required secrets (OPENAI_API_KEY, GROQ_API_KEY) have no defaults
    and will raise a validation error at startup if not set.
    This follows the security rule: validate required secrets at startup.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = Field(default="keepcontext-ai", description="Application name")
    APP_VERSION: str = Field(default="0.1.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # --- ChromaDB ---
    CHROMA_HOST: str = Field(default="localhost", description="ChromaDB host")
    CHROMA_PORT: int = Field(default=8100, description="ChromaDB port")

    # --- OpenAI (embeddings) ---
    OPENAI_API_KEY: str = Field(description="OpenAI API key for embeddings")
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model name",
    )

    # --- Groq (LLM inference) ---
    GROQ_API_KEY: str = Field(description="Groq API key for LLM inference")
    GROQ_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model name for LLM inference",
    )
    GROQ_MAX_TOKENS: int = Field(
        default=2048,
        description="Maximum tokens for Groq LLM response",
    )

    # --- Neo4j (knowledge graph) ---
    NEO4J_URI: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j connection URI",
    )
    NEO4J_USER: str = Field(
        description="Neo4j username",
    )
    NEO4J_PASSWORD: str = Field(
        description="Neo4j password",
    )

    # --- Agent system ---
    AGENT_MAX_STEPS: int = Field(
        default=3,
        description="Maximum review-loop iterations for agent workflow",
    )
    AGENT_TIMEOUT: int = Field(
        default=120,
        description="Agent workflow timeout in seconds",
    )


def get_settings() -> Settings:
    """Create and return a validated Settings instance.

    Raises:
        ValidationError: If required environment variables are missing.
    """
    return Settings()  # type: ignore[call-arg]
