# Production Go-Live Checklist

This checklist covers the non-testing work required before launching KeepContext AI to production.

## Owners

Use these owner labels in your tracker:

- Platform: container build, deployment, runtime config
- Backend: app configuration, API behavior, readiness/health
- Security: secrets, policy checks, vulnerability review
- DevOps: CI/CD gates, rollback automation, monitoring setup

## Exit Criteria

Go-live is approved only when every item below is marked complete and has evidence (logs, screenshots, command output, or ticket links).

## 1. Secrets and Configuration

Owner: Security + Platform

- [ ] Rotate any previously exposed OpenAI/Groq keys.
- [ ] Store all production secrets in your secret manager.
- [ ] Ensure deployment environment provides these required variables:
  - `OPENAI_API_KEY`
  - `GROQ_API_KEY`
  - `NEO4J_USER`
  - `NEO4J_PASSWORD`

PowerShell validation command:

```powershell
$required = @('OPENAI_API_KEY','GROQ_API_KEY','NEO4J_USER','NEO4J_PASSWORD')
$missing = $required | Where-Object { -not $env:$_ }
if ($missing.Count -gt 0) { throw "Missing env vars: $($missing -join ', ')" }
"All required env vars are present"
```

## 2. Container Build and Runtime Baseline

Owner: Platform

- [ ] Build production image from clean state.
- [ ] Verify container starts with non-root user.
- [ ] Confirm runtime ports and health checks are correct.

Commands:

```powershell
docker-compose build --no-cache
docker-compose up -d
docker ps
docker logs keepcontext-ai --tail 100
```

## 3. Service Health and Smoke Validation

Owner: Backend

- [ ] API health returns healthy.
- [ ] Core memory endpoint responds.
- [ ] Context query endpoint responds.

Commands:

```powershell
Invoke-RestMethod http://localhost:8003/health

Invoke-RestMethod -Method Post http://localhost:8003/api/v1/memory `
  -ContentType 'application/json' `
  -Body '{"content":"Production smoke memory","memory_type":"documentation"}'

Invoke-RestMethod -Method Post http://localhost:8003/api/v1/context/query `
  -ContentType 'application/json' `
  -Body '{"query":"Production smoke","top_k":3}'
```

## 4. Security Controls

Owner: Security

- [ ] Confirm no secrets are committed in repository history for current release branch.
- [ ] Scan dependencies for known vulnerabilities.
- [ ] Validate API error responses do not leak internal secrets.

Commands:

```powershell
git grep -n "sk-|gsk_|OPENAI_API_KEY=|GROQ_API_KEY="

$venvPy = "c:\Users\Aashish kumar\Videos\keepcontext-ai\venv\Scripts\python.exe"
& $venvPy -m pip install pip-audit
& $venvPy -m pip_audit
```

## 5. Observability and Alerts

Owner: DevOps

- [ ] Centralized logs enabled for app + ChromaDB + Neo4j.
- [ ] Alerts configured for:
  - elevated 5xx rate
  - high latency on `/health` and `/api/v1/context/query`
  - repeated container restarts
- [ ] Dashboard created with request rate, latency, error rate.

## 6. Backup and Recovery

Owner: Platform + DevOps

- [ ] Chroma volume backup procedure documented and tested.
- [ ] Neo4j data backup and restore tested.
- [ ] Recovery time objective and recovery point objective documented.

## 7. Rollout and Rollback Plan

Owner: Platform + DevOps

- [ ] Define rollout strategy (all-at-once or staged).
- [ ] Define rollback trigger thresholds.
- [ ] Validate rollback command path.

Commands:

```powershell
# Tag image before release
docker tag keepcontext-ai:latest keepcontext-ai:release-YYYYMMDD

# Example rollback (replace with your registry/tag process)
docker-compose down
docker-compose up -d
```

## 8. Final Launch Approval

Owner: Engineering Lead

- [ ] Security sign-off complete.
- [ ] Platform sign-off complete.
- [ ] Backend sign-off complete.
- [ ] Incident contact/on-call owner assigned.

If any item is incomplete, launch is blocked.
