"""Embedding pipeline for KeepContext AI.

Converts text content into vector embeddings using OpenAI's API.

Usage:
    from keepcontext_ai.embeddings import EmbeddingService

    service = EmbeddingService(api_key="sk-...")
    embedding = service.generate("Authentication uses JWT tokens")
"""

from keepcontext_ai.embeddings.embedding_service import EmbeddingService

__all__ = [
    "EmbeddingService",
]
