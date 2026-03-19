# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) and other AI assistants
when working with code in this repository.

## Project Overview

**KeepContext AI** (ProjectScope AI+) is a persistent AI memory and orchestration platform
for software development. It allows multiple AI tools (ChatGPT, Claude, Cursor, Copilot)
to share a unified understanding of a project by storing architecture decisions, code context,
project documentation, tasks, and relationships between components.

**Tech Stack:** Python 3.10+ · FastAPI · ChromaDB · LangGraph · OpenAI Embeddings · Groq LLM

## Running the App

```bash
# Setup
uv venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux
uv pip install -e ".[dev]"

# Run
make run                       # starts uvicorn on http://localhost:8000

# Docker
docker-compose up --build
```

## Running Tests

```bash
# All tests with coverage
make test

# Or directly
pytest --cov=src --cov-report=term-missing

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v
```

## Architecture

```
src/keepcontext_ai/
├── main.py                    # FastAPI entry point
├── config.py                  # Pydantic BaseSettings (env-based)
├── api/                       # API layer
│   └── routes/                # REST endpoints
│       ├── health.py          # Health check
│       ├── memory.py          # Memory CRUD (/api/v1/memory)
│       └── context.py         # Context retrieval (/api/v1/context)
├── memory/                    # Memory layer (ChromaDB)
│   ├── chroma_client.py       # ChromaDB wrapper
│   └── schemas.py             # Memory Pydantic models
├── embeddings/                # Embedding pipeline
│   └── embedding_service.py   # OpenAI embedding service
├── context/                   # Context retrieval engine
│   └── retrieval.py           # Semantic search
├── agents/                    # LangGraph agents (Phase 3)
└── exceptions/                # Custom exception hierarchy
    └── base.py                # AppError → MemoryError → EmbeddingError
```

## Critical Rules

### 1. Code Organization

- Many small files over few large files
- High cohesion, low coupling
- 200-400 lines typical, 800 max per file
- Functions < 50 lines
- No deep nesting (> 4 levels)
- Organize by feature/domain, not by type

### 2. Python Code Style

- Follow **PEP 8** conventions
- **Type annotations** on ALL function signatures
- **Immutability** — use `@dataclass(frozen=True)` or Pydantic `model_config = {"frozen": True}`
- **black** for formatting, **isort** for imports, **ruff** for linting, **mypy** strict
- EAFP pattern — prefer try/except over checking conditions
- No mutable default arguments
- Use `is None` not `== None`
- Explicit imports, never `from module import *`

### 3. Error Handling

- Custom exception hierarchy: `AppError → MemoryError / EmbeddingError / ContextError`
- Catch specific exceptions, never bare `except:`
- Chain exceptions with `from e`
- User-friendly messages in API responses
- Detailed error context in server logs
- Never silently swallow errors

### 4. API Design

- Resource-based URLs: `/api/v1/{resource}`
- Consistent response envelope: `{"data": ...}` or `{"error": {"code": ..., "message": ...}}`
- Proper HTTP status codes (not 200 for everything)
- Input validation with Pydantic schemas
- Pagination for list endpoints

### 5. Testing

- TDD: Write tests first (RED → GREEN → REFACTOR)
- 80% minimum coverage
- Unit tests for services and utilities
- Integration tests for API endpoints
- Use pytest fixtures and conftest.py

### 6. Security

- No hardcoded secrets — environment variables only
- Validate required secrets at startup
- Validate all user inputs at system boundaries
- Error messages don't leak sensitive data
- Never commit `.env` files

## Key Patterns

### API Response Envelope

```python
# Success
{"data": {"id": "abc-123", "content": "..."}}

# Collection with pagination
{"data": [...], "meta": {"total": 42, "page": 1, "per_page": 20}}

# Error
{"error": {"code": "validation_error", "message": "Content is required"}}
```

### Service Layer Pattern

```python
class MemoryService:
    def __init__(self, chroma_client: ChromaClient, embedding_service: EmbeddingService):
        self._chroma = chroma_client
        self._embeddings = embedding_service

    async def store(self, entry: MemoryCreate) -> MemoryEntry:
        embedding = await self._embeddings.generate(entry.content)
        return await self._chroma.store(entry, embedding)
```

### Exception Pattern

```python
class AppError(Exception):
    def __init__(self, message: str, code: str = "internal_error"):
        self.message = message
        self.code = code
        super().__init__(message)

class MemoryError(AppError):
    pass
```

## Environment Variables

```bash
# Required
OPENAI_API_KEY=           # OpenAI API key for embeddings
GROQ_API_KEY=             # Groq API key for LLM inference

# Optional
APP_NAME=keepcontext-ai
APP_VERSION=0.1.0
DEBUG=false
LOG_LEVEL=INFO
CHROMA_HOST=localhost
CHROMA_PORT=8100
```

## Git Workflow

- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `perf:`, `ci:`
- Never commit to main directly
- All tests must pass before merge
- PRs require review

## Implementation Phases

- **Phase 1** (current): Core Memory System — FastAPI + ChromaDB + Embedding pipeline
- **Phase 2**: Graph Knowledge — Neo4j + relationship storage + architecture queries
- **Phase 3**: Agent System — LangGraph planner, developer, reviewer agents
- **Phase 4**: Developer Tools — VS Code extension
- **Phase 5**: Production — AWS deploy, CI/CD, auth, monitoring
