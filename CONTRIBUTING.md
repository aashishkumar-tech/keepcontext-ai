# Contributing to KeepContext AI

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/keepcontext-ai.git
cd keepcontext-ai

# Create virtual environment
uv venv .venv
.\.venv\Scripts\Activate.ps1    # Windows
source .venv/bin/activate        # macOS/Linux

# Install all dependencies (prod + dev)
uv pip install -r requirements.txt
uv pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

## Running Tests

```bash
# All tests with coverage
make test

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_workflow.py -v
```

## Code Standards

### Style
- **PEP 8** conventions enforced by `ruff`
- **black** for formatting (line length 88)
- **isort** for import ordering (black profile)
- **mypy** strict mode for type checking

### Rules
- Type annotations on **all** function signatures
- Docstrings on **all** public functions and classes
- Functions under **50 lines**
- Files under **400 lines** (800 max)
- Custom exceptions, never bare `except:`
- Dependency injection over global state
- Immutable models (`frozen=True`)

### Linting & Formatting

```bash
# Check
make lint

# Auto-fix
make format
```

## Git Workflow

1. Create a branch from `develop`: `git checkout -b feat/your-feature develop`
2. Write tests first (TDD)
3. Implement the feature
4. Ensure all tests pass: `make test`
5. Ensure lint passes: `make lint`
6. Commit with conventional commits:
   - `feat:` — new feature
   - `fix:` — bug fix
   - `refactor:` — code restructuring
   - `docs:` — documentation only
   - `test:` — test additions/changes
   - `chore:` — build/tooling changes
7. Open a PR against `develop`

## Project Structure

```
src/keepcontext_ai/
├── main.py              # FastAPI entry point
├── config.py            # Settings (env-based)
├── api/routes/          # REST endpoints
├── memory/              # ChromaDB vector storage
├── embeddings/          # OpenAI embedding pipeline
├── context/             # Context retrieval engine
├── graph/               # Neo4j knowledge graph
├── llm/                 # Groq LLM inference
├── agents/              # LangGraph agent workflow
└── exceptions/          # Custom exception hierarchy
```

## Adding a New Feature

1. **Add schemas** in the relevant `schemas.py`
2. **Add service logic** in the appropriate module
3. **Add API route** in `api/routes/`
4. **Register the router** in `main.py`
5. **Write unit tests** in `tests/unit/`
6. **Write integration tests** in `tests/integration/`
7. **Update documentation** in `README.md` and `docs/`

## Questions?

Open an issue on GitHub for discussion.
