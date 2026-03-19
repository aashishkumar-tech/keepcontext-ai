# Development Guide

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker & Docker Compose (for ChromaDB)
- Git

## Setup

### 1. Clone and Create Environment

```bash
git clone https://github.com/your-username/keepcontext-ai.git
cd keepcontext-ai

# Using uv (recommended)
uv venv venv
venv\Scripts\activate           # Windows
source venv/bin/activate        # macOS/Linux
uv pip install -e ".[dev]"

# Or using pip
python -m venv venv
venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings | Yes |
| `GROQ_API_KEY` | Groq API key for LLM inference | Yes |
| `NEO4J_USER` | Neo4j username for graph DB | Yes |
| `NEO4J_PASSWORD` | Neo4j password for graph DB | Yes |
| `CHROMA_HOST` | ChromaDB host | No (default: `localhost`) |
| `CHROMA_PORT` | ChromaDB port | No (default: `8100`) |
| `DEBUG` | Enable debug mode | No (default: `false`) |
| `LOG_LEVEL` | Logging level | No (default: `INFO`) |

### 3. Start Services

```bash
# Start ChromaDB via Docker
docker-compose up -d

# Start the API server
make run
# or
uvicorn src.keepcontext_ai.main:app --host 0.0.0.0 --port 8000 --reload
```

## Development Workflow

### TDD Process (Mandatory)

Every feature follows this cycle:

```
1. Write test first (RED)     → Test should FAIL
2. Implement minimal code (GREEN)  → Test should PASS
3. Refactor (IMPROVE)         → Clean up, verify 80%+ coverage
```

### Code Quality Commands

| Command | Description |
|---------|-------------|
| `make test` | Run tests with coverage |
| `make lint` | Run ruff + mypy |
| `make format` | Auto-format with black + isort |
| `make run` | Start the application |
| `make clean` | Remove build artifacts |

### Manual Commands

```bash
# Formatting
black .
isort .

# Linting
ruff check .

# Type checking
mypy src/

# Tests with coverage
pytest --cov=src --cov-report=term-missing

# Security scanning
bandit -r src/
```

## API Endpoints

### Health

```
GET /health
→ {"status": "healthy", "version": "0.1.0"}
```

### Memory (Phase 1)

```
POST   /api/v1/memory          → Store a memory entry
GET    /api/v1/memory           → List memory entries
GET    /api/v1/memory/:id       → Get a specific entry
DELETE /api/v1/memory/:id       → Delete a memory entry
```

### Context (Phase 1)

```
POST   /api/v1/context/query    → Query context with natural language
```

## Project Phases

### Phase 1: Core Memory System (Current)

- [x] FastAPI backend scaffold
- [ ] ChromaDB integration
- [ ] OpenAI embedding pipeline
- [ ] Memory CRUD endpoints
- [ ] Context retrieval endpoint
- [ ] Unit tests (80%+ coverage)

### Phase 2: Graph Knowledge

- [ ] Neo4j integration
- [ ] Relationship storage (component → depends_on → component)
- [ ] Architecture query endpoints

### Phase 3: Agent System

- [ ] LangGraph integration
- [ ] Planner agent
- [ ] Developer agent
- [ ] Reviewer agent
- [ ] Context manager agent

### Phase 4: Developer Tools

- [ ] VS Code extension

### Phase 5: Production

- [ ] AWS deployment
- [ ] CI/CD pipeline
- [ ] Authentication (JWT)
- [ ] Rate limiting
- [ ] Monitoring & logging

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | FastAPI | Async, auto-docs, Pydantic integration |
| Vector DB | ChromaDB | Simple, local-first, Python-native |
| Graph DB | Neo4j (Phase 2) | Industry standard for relationship graphs |
| Agent Framework | LangGraph (Phase 3) | State machines for agent workflows |
| Embeddings | OpenAI | High quality, widely supported |
| LLM | Groq | Fast inference, low latency |
| Config | Pydantic BaseSettings | Type-safe, env-based, validation at startup |

## Commit Convention

```
feat: add memory storage endpoint
fix: handle empty embedding response
refactor: extract embedding logic to service
docs: update API documentation
test: add memory service unit tests
chore: update dependencies
perf: optimize vector search query
ci: add GitHub Actions workflow
```
