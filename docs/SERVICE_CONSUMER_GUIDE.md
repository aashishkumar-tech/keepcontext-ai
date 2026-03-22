# Service Consumer Guide

This guide is for users who consume KeepContext AI as a hosted service.
You do not need to clone the repository or deploy infrastructure.

## What You Need

- A KeepContext AI service base URL from the service owner
- API access details if your deployment requires authentication
- VS Code (optional) for extension-based usage

## 1. Verify Service Health

```bash
BASE_URL=http://<your-service-host>:8003
curl "$BASE_URL/health"
```

Expected response should indicate healthy service dependencies.

## 2. Store Memory via API

```bash
curl -X POST "$BASE_URL/api/v1/memory" \
  -H "Content-Type: application/json" \
  -d '{"content":"Auth uses JWT with RS256","memory_type":"decision"}'
```

## 3. Query Context via API

```bash
curl -X POST "$BASE_URL/api/v1/context/query" \
  -H "Content-Type: application/json" \
  -d '{"query":"How does authentication work?","top_k":5}'
```

## 4. Use With VS Code Extension

1. Install the KeepContext AI extension.
2. Open VS Code settings.
3. Set `keepcontext.apiUrl` to your service URL.
4. Run `KeepContext: Query Context` from Command Palette.

## 5. Common Consumer Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Connection error in extension | Wrong service URL | Update `keepcontext.apiUrl` |
| Health endpoint unreachable | Service down or blocked network | Contact service owner, verify URL and firewall |
| Empty retrieval results | No memories stored yet | Store memories first, then query |
| API returns auth error | Missing/invalid access credentials | Use valid service credentials |

## 6. Response Contract and Error Handling

Most endpoints follow a predictable JSON shape so clients can parse responses consistently.

Success example:

```json
{
  "data": {
    "id": "mem_123",
    "content": "Auth uses JWT with RS256",
    "memory_type": "decision"
  }
}
```

Error example:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid memory_type value"
  }
}
```

Recommended client behavior:

- Treat 2xx responses as success and parse `data`.
- Treat 4xx responses as client-actionable errors and show `error.message`.
- Treat 5xx responses as transient service issues and retry with backoff.
- For write operations, use idempotency safeguards in your client when retrying.

## Consumer vs Maintainer Docs

- Consumer: this guide and root README service sections
- Maintainer: deployment and infrastructure guides under `deploy/aws/`
