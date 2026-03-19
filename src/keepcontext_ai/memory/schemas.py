"""Pydantic models and enums for the memory layer.

Defines the data contracts for storing, retrieving, and querying
memory entries in KeepContext AI.
"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MemoryType(str, Enum):
    """Types of memory entries that can be stored.

    Each type represents a different category of project knowledge.
    """

    CONVERSATION = "conversation"
    CODE = "code"
    DECISION = "decision"
    DOCUMENTATION = "documentation"


class MemoryCreate(BaseModel):
    """Request model for creating a new memory entry.

    Attributes:
        content: The text content to store and embed.
        memory_type: Category of this memory entry.
        metadata: Optional key-value metadata (e.g., file path, author).
    """

    model_config = ConfigDict(frozen=True)

    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Text content to store and embed",
    )
    memory_type: MemoryType = Field(
        default=MemoryType.DOCUMENTATION,
        description="Category of this memory entry",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Optional key-value metadata",
    )


class MemoryEntry(BaseModel):
    """Full memory entry as stored in the database.

    Returned when retrieving a specific memory entry by ID
    or when listing entries.

    Attributes:
        id: Unique identifier for this entry.
        content: The stored text content.
        memory_type: Category of this entry.
        metadata: Key-value metadata.
        created_at: Timestamp when the entry was created.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique identifier")
    content: str = Field(..., description="Stored text content")
    memory_type: MemoryType = Field(..., description="Category of this entry")
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Key-value metadata",
    )
    created_at: str = Field(
        ...,
        description="ISO 8601 timestamp of creation",
    )


class MemoryQuery(BaseModel):
    """Request model for querying memory with natural language.

    Attributes:
        query: Natural language query string.
        top_k: Maximum number of results to return.
        memory_type: Optional filter by memory type.
    """

    model_config = ConfigDict(frozen=True)

    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Natural language query",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of results to return",
    )
    memory_type: MemoryType | None = Field(
        default=None,
        description="Optional filter by memory type",
    )


class MemoryResult(BaseModel):
    """A single search result from a memory query.

    Attributes:
        entry: The matching memory entry.
        score: Relevance score (0.0 to 1.0, higher is more relevant).
    """

    model_config = ConfigDict(frozen=True)

    entry: MemoryEntry = Field(..., description="The matching memory entry")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score (0.0 to 1.0)",
    )


def create_timestamp() -> str:
    """Create an ISO 8601 UTC timestamp string.

    Returns:
        Current UTC time as ISO 8601 string.
    """
    return datetime.now(timezone.utc).isoformat()
