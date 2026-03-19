# KeepContext AI — Agent Instructions

This is a **persistent AI memory platform** for software development.
It stores project knowledge (architecture, code, decisions) and provides
semantic retrieval so AI tools never lose context.

## Core Principles

1. **Immutability** — Always create new objects, never mutate existing ones
2. **Test-Driven** — Write tests before implementation, 80%+ coverage required
3. **Security-First** — Never compromise on security; validate all inputs
4. **Plan Before Execute** — Plan complex features before writing code
5. **Type Safety** — Type annotations on every function signature

## Coding Style

**Immutability (CRITICAL):** Always create new objects, never mutate.
Use `@dataclass(frozen=True)` or Pydantic frozen models.

**File organization:** Many small files over few large ones.
200-400 lines typical, 800 max. Functions < 50 lines.
Organize by feature/domain, not by type.

**Error handling:** Handle errors at every level. Provide user-friendly
messages in API responses. Log detailed context server-side.
Never silently swallow errors. Use custom exception hierarchy.

**Input validation:** Validate all user input at system boundaries.
Use Pydantic schemas. Fail fast with clear messages.
Never trust external data.

## Python Standards

- PEP 8 conventions
- Type annotations on ALL function signatures
- `black` for formatting (line-length 88)
- `isort` for import sorting (profile: black)
- `ruff` for linting
- `mypy` strict mode for type checking
- EAFP pattern (try/except over pre-checks)
- No mutable default arguments
- Specific exception catching (never bare `except:`)
- Exception chaining with `from e`
- Import order: stdlib → third-party → local

## API Design

- RESTful resource-based URLs: `/api/v1/{resource}`
- Response envelope: `{"data": ...}` for success, `{"error": {"code": ..., "message": ...}}` for errors
- Proper HTTP status codes (201 Created, 404 Not Found, 422 Unprocessable Entity, etc.)
- Input validation with Pydantic request models
- Pagination with `meta` for list endpoints

## Testing Requirements

**Minimum coverage: 80%**

Test types (all required):
1. **Unit tests** — Individual functions, services, utilities
2. **Integration tests** — API endpoints, database operations

**TDD workflow (mandatory):**
1. Write test first (RED) — test should FAIL
2. Write minimal implementation (GREEN) — test should PASS
3. Refactor (IMPROVE) — verify coverage 80%+

## Security Guidelines

**Before ANY commit:**
- No hardcoded secrets (API keys, passwords, tokens)
- All user inputs validated with Pydantic
- Error messages don't leak sensitive data
- Environment variables for all secrets
- Validate required secrets at startup

**If security issue found:** STOP → fix CRITICAL issues → rotate exposed secrets.

## Git Workflow

**Commit format:** `<type>: <description>`

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

**PR workflow:** Analyze full commit history → draft comprehensive summary →
include test plan → all tests must pass.

## Project Structure

```
src/keepcontext_ai/
├── main.py              — FastAPI entry point
├── config.py            — Pydantic settings
├── api/routes/          — REST API endpoints
├── memory/              — ChromaDB vector storage
├── embeddings/          — OpenAI embedding pipeline
├── context/             — Semantic retrieval engine
├── agents/              — LangGraph agents (Phase 3)
└── exceptions/          — Custom exception hierarchy
tests/
├── unit/                — Unit tests
└── integration/         — Integration tests
```

## Success Metrics

- All tests pass with 80%+ coverage
- No security vulnerabilities
- Code is readable and maintainable
- Type checking passes (mypy strict)
- Formatting passes (black + isort)
- Linting passes (ruff)
