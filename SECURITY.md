# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Reporting a Vulnerability

If you discover a security vulnerability in KeepContext AI, please report it responsibly:

1. **Do NOT** open a public GitHub issue.
2. Email the maintainers with a description of the vulnerability.
3. Include steps to reproduce and any relevant details.

We will respond within 48 hours and work with you to resolve the issue.

## Security Practices

- **No hardcoded secrets** — all sensitive values loaded from environment variables.
- **Required secrets validated at startup** — the app fails fast if `OPENAI_API_KEY`, `GROQ_API_KEY`, `NEO4J_USER`, or `NEO4J_PASSWORD` are missing.
- **Input validation** — all user inputs validated with Pydantic schemas at API boundaries.
- **Error messages** — internal details are logged server-side; API responses use generic error codes.
- **`.env` files** — excluded from version control via `.gitignore`.
- **Non-root Docker user** — the container runs as `appuser`, not root.
- **Dependency pinning** — minimum versions specified in `requirements.txt` and `pyproject.toml`.
