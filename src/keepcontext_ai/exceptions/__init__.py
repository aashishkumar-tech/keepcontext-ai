"""Custom exceptions for KeepContext AI.

Import exceptions directly from this package:
    from keepcontext_ai.exceptions import AppError, MemoryError
"""

from keepcontext_ai.exceptions.base import (
    AgentError,
    AppError,
    ContextError,
    EmbeddingError,
    EvaluationError,
    GraphError,
    LLMError,
    MemoryError,
)

__all__ = [
    "AgentError",
    "AppError",
    "ContextError",
    "EmbeddingError",
    "EvaluationError",
    "GraphError",
    "LLMError",
    "MemoryError",
]
