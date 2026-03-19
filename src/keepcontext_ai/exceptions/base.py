"""Custom exception hierarchy for KeepContext AI.

Exception tree:
    AppError (base)
    ├── MemoryError        — ChromaDB / storage failures
    ├── EmbeddingError     — OpenAI embedding failures
    ├── ContextError       — Context retrieval failures
    ├── GraphError         — Neo4j / knowledge graph failures
    ├── LLMError           — Groq LLM inference failures
    └── AgentError         — Agent workflow failures

Usage:
    from keepcontext_ai.exceptions import MemoryError, GraphError, AgentError

    try:
        result = chroma_client.store(entry, embedding)
    except chromadb.errors.ChromaError as e:
        raise MemoryError("Failed to store memory entry") from e
"""


class AppError(Exception):
    """Base exception for all KeepContext AI application errors.

    Attributes:
        message: Human-readable error description.
        code: Machine-readable error code for API responses.
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: str = "internal_error",
    ) -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


class MemoryError(AppError):
    """Raised when a memory storage operation fails.

    Examples: ChromaDB connection errors, storage failures,
    invalid collection operations.
    """

    def __init__(
        self,
        message: str = "Memory operation failed",
        code: str = "memory_error",
    ) -> None:
        super().__init__(message=message, code=code)


class EmbeddingError(AppError):
    """Raised when embedding generation fails.

    Examples: OpenAI API errors, rate limits, invalid input,
    network failures.
    """

    def __init__(
        self,
        message: str = "Embedding generation failed",
        code: str = "embedding_error",
    ) -> None:
        super().__init__(message=message, code=code)


class ContextError(AppError):
    """Raised when context retrieval fails.

    Examples: Query processing errors, no results found,
    retrieval pipeline failures.
    """

    def __init__(
        self,
        message: str = "Context retrieval failed",
        code: str = "context_error",
    ) -> None:
        super().__init__(message=message, code=code)


class GraphError(AppError):
    """Raised when a knowledge graph operation fails.

    Examples: Neo4j connection errors, query failures,
    invalid entity/relationship operations.
    """

    def __init__(
        self,
        message: str = "Graph operation failed",
        code: str = "graph_error",
    ) -> None:
        super().__init__(message=message, code=code)


class LLMError(AppError):
    """Raised when LLM inference fails.

    Examples: Groq API errors, rate limits, invalid prompts,
    response parsing failures.
    """

    def __init__(
        self,
        message: str = "LLM inference failed",
        code: str = "llm_error",
    ) -> None:
        super().__init__(message=message, code=code)


class AgentError(AppError):
    """Raised when an agent workflow fails.

    Examples: Planning failures, code generation errors,
    review loop timeouts, workflow orchestration failures.
    """

    def __init__(
        self,
        message: str = "Agent workflow failed",
        code: str = "agent_error",
    ) -> None:
        super().__init__(message=message, code=code)


class EvaluationError(AppError):
    """Raised when a quality evaluation workflow fails.

    Examples: retrieval benchmark failures, groundedness scoring errors,
    or agent quality evaluation failures.
    """

    def __init__(
        self,
        message: str = "Evaluation workflow failed",
        code: str = "evaluation_error",
    ) -> None:
        super().__init__(message=message, code=code)
