"""FastAPI application entry point.

Initializes the app, registers routers, sets up global error handling,
and wires together services on startup.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from keepcontext_ai.api.routes import (
    agents,
    ask,
    context,
    evaluation,
    graph,
    health,
    memory,
)
from keepcontext_ai.config import Settings, get_settings
from keepcontext_ai.context import ContextRetriever
from keepcontext_ai.embeddings import EmbeddingService
from keepcontext_ai.exceptions import (
    AppError,
    GraphError,
    LLMError,
)
from keepcontext_ai.graph import KnowledgeGraphClient
from keepcontext_ai.llm import GroqLLMService
from keepcontext_ai.memory import ChromaMemoryClient

logger = logging.getLogger(__name__)


def _init_services(app: FastAPI, settings: Settings) -> None:
    """Initialize application services and attach to app state.

    Args:
        app: The FastAPI application instance.
        settings: Validated application settings.
    """
    app.state.settings = settings

    app.state.chroma = ChromaMemoryClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
    )
    logger.info(
        "ChromaDB connected at %s:%s",
        settings.CHROMA_HOST,
        settings.CHROMA_PORT,
    )

    app.state.embeddings = EmbeddingService(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_EMBEDDING_MODEL,
    )
    logger.info(
        "Embedding service initialized (model: %s)", settings.OPENAI_EMBEDDING_MODEL
    )

    # --- Neo4j knowledge graph (optional — degrade gracefully) ---
    try:
        app.state.graph = KnowledgeGraphClient(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD,
        )
        logger.info("Neo4j connected at %s", settings.NEO4J_URI)
    except GraphError:
        app.state.graph = None
        logger.warning("Neo4j unavailable — graph features disabled")

    # --- Groq LLM service (optional — degrade gracefully) ---
    try:
        app.state.llm = GroqLLMService(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            max_tokens=settings.GROQ_MAX_TOKENS,
        )
        logger.info("Groq LLM service initialized (model: %s)", settings.GROQ_MODEL)
    except LLMError:
        app.state.llm = None
        logger.warning("Groq LLM unavailable — ask features disabled")

    app.state.retriever = ContextRetriever(
        chroma_client=app.state.chroma,
        embedding_service=app.state.embeddings,
        graph_client=app.state.graph,
        llm_service=app.state.llm,
    )
    logger.info("Context retriever initialized")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler for startup and shutdown.

    Initializes all services on startup and logs shutdown.
    """
    settings = get_settings()
    _init_services(app, settings)
    logger.info("%s v%s started", settings.APP_NAME, settings.APP_VERSION)
    yield
    # Shutdown: close external connections
    if hasattr(app.state, "graph") and app.state.graph is not None:
        app.state.graph.close()
        logger.info("Neo4j connection closed")
    logger.info("%s shutting down", settings.APP_NAME)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A fully configured FastAPI instance with routers and error handlers.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # --- Register routers ---
    app.include_router(health.router)
    app.include_router(memory.router)
    app.include_router(context.router)
    app.include_router(graph.router)
    app.include_router(ask.router)
    app.include_router(agents.router)
    app.include_router(evaluation.router)

    # --- Global exception handlers ---

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Handle all application errors with consistent JSON envelope."""
        status_code = 500

        if exc.code == "memory_not_found":
            status_code = 404
        elif exc.code == "graph_not_found":
            status_code = 404
        elif exc.code in ("embedding_empty_input", "embedding_empty_batch"):
            status_code = 422
        elif exc.code in ("llm_empty_input",):
            status_code = 422
        elif exc.code in ("memory_connection_error", "embedding_init_error"):
            status_code = 503
        elif exc.code in ("graph_connection_error", "llm_init_error"):
            status_code = 503
        elif exc.code in ("llm_api_error", "llm_unexpected_error"):
            status_code = 502
        elif exc.code in ("agent_error", "evaluation_dependency_error"):
            status_code = 503

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                },
            },
        )

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {"message": f"Welcome to {settings.APP_NAME}"}

    return app


def get_app() -> FastAPI:
    """Lazy app singleton for uvicorn / production use.

    Returns the app instance, creating it on first call.
    This avoids calling get_settings() at import time,
    which would fail in test environments without env vars.
    """
    global _app  # noqa: PLW0603
    if _app is None:
        _app = create_app()
    return _app


_app: FastAPI | None = None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "keepcontext_ai.main:get_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        factory=True,
    )
