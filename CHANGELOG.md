# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-11

### Added

#### Phase 1 — Core Memory System
- FastAPI application with health check, memory CRUD, and context query endpoints
- ChromaDB integration for persistent vector storage
- OpenAI `text-embedding-3-small` embedding pipeline
- Pydantic-based configuration with environment variable support
- Custom exception hierarchy (`AppError` → `MemoryError`, `EmbeddingError`, `ContextError`)
- Docker Compose setup with ChromaDB service
- Unit and integration tests (82%+ coverage)

#### Phase 2 — Knowledge Graph & LLM
- Neo4j knowledge graph for entity and relationship storage
- Entity and relationship extraction from text
- Groq LLM integration (`llama-3.3-70b-versatile`) for intelligent answers
- Enriched context retrieval combining vector + graph + LLM
- `/api/v1/graph` endpoints for entity and relationship management
- `/api/v1/ask` endpoint for context-aware question answering
- Extended exception hierarchy (`GraphError`, `LLMError`)
- Docker Compose updated with Neo4j service

#### Phase 3 — Agent System
- LangGraph multi-agent workflow (plan → develop → review loop)
- Context Manager agent for retrieving relevant project knowledge
- Planner agent for structured task plan generation
- Developer agent for code implementation generation
- Reviewer agent for automated code review
- Conditional review loop with configurable max iterations
- `/api/v1/agents/run`, `/plan`, `/review` endpoints
- `AgentError` exception class
- Full unit and integration test coverage for all agent modules

### Infrastructure
- GitHub Actions CI pipeline (Python 3.10–3.12)
- Makefile with install, test, lint, format, run, docker commands
- `.env.example` with all required configuration variables
