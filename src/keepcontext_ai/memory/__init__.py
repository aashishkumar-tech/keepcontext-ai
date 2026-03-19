"""Memory layer for KeepContext AI.

Provides ChromaDB-backed vector storage for project knowledge
including conversations, code, decisions, and documentation.

Usage:
    from keepcontext_ai.memory import ChromaMemoryClient, MemoryCreate, MemoryType

    client = ChromaMemoryClient(host="localhost", port=8100)
    entry = MemoryCreate(content="Auth uses JWT", memory_type=MemoryType.DECISION)
    stored = client.store(entry, embedding=[0.1, 0.2, ...])
"""

from keepcontext_ai.memory.chroma_client import ChromaMemoryClient
from keepcontext_ai.memory.schemas import (
    MemoryCreate,
    MemoryEntry,
    MemoryQuery,
    MemoryResult,
    MemoryType,
)

__all__ = [
    "ChromaMemoryClient",
    "MemoryCreate",
    "MemoryEntry",
    "MemoryQuery",
    "MemoryResult",
    "MemoryType",
]
