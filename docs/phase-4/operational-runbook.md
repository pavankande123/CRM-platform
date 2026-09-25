# ENERMAX CRM — PHASE 4 OPERATIONAL RUNBOOK

**Target Audience**: DevOps Engineers, Site Reliability Engineers (SRE), SaaS Platform Operators  
**Date**: September 25, 2026  
**Status**: APPROVED & OPERATIONAL  

---

## 1. Service Health & Diagnostic Probes

| Endpoint | Probe Type | Target Status | Failure Action |
| :--- | :--- | :--- | :--- |
| `GET /health` | Liveness | HTTP 200 `{"status": "ok"}` | Process hung/crashed. Container orchestrator will restart pod/container. |
| `GET /ready` | Readiness | HTTP 200 `{"status": "ready"}` | Critical dependency (PostgreSQL) down. Container removed from load balancer routing. |
| `GET /metrics` | Telemetry | HTTP 200 (Prometheus text) | Alert monitoring system if endpoint is unresponsive or reports 5xx spikes. |

---

## 2. Emergency Operational Playbooks

### Playbook A: PostgreSQL High Connection Count / Saturation
**Symptoms**:
- `enermax_db_pool_checked_out` approaching `DB_POOL_SIZE + DB_MAX_OVERFLOW` (30).
- Latency spikes on `p95` > 500ms.
- 500 errors in logs mentioning `TimeoutError` or `pool timeout`.

**Remediation Steps**:
1. Check active database locks and long-running queries:
   ```sql
   SELECT pid, now() - query_start AS duration, query, state
   FROM pg_stat_activity
   WHERE state != 'idle' AND (now() - query_start) > interval '5 seconds';
   ```
2. Terminate runaway transaction:
   ```sql
   SELECT pg_terminate_backend(<pid>);
   ```
3. Statement timeout (`DB_STATEMENT_TIMEOUT=15000`) will automatically cancel any query exceeding 15 seconds.
4. If sustained traffic exceeds capacity, adjust PgBouncer pool or increase `DB_POOL_SIZE` in `.env.production`.

---

### Playbook B: Redis Outage / Unavailability
**Symptoms**:
- Logs emit `WARNING: Redis connection failed. Operating in graceful in-memory fallback mode.`
- `/ready` returns `"dependencies": {"redis": {"status": "degraded"}}`.

**Impact & Self-Healing**:
- **API Impact**: Zero downtime. CRM requests continue without error.
- **Rate Limiting**: Automatically falls back to in-process sliding window.
- **Token Revocation**: Automatically falls back to local memory store.
- **Recovery Action**:
  ```bash
  docker compose restart redis
  # Or check Redis container logs:
  docker compose logs --tail=100 redis
  ```
- The backend's `RedisManager` periodically probes Redis and automatically restores full distributed caching once Redis resumes.

---

### Playbook C: Background Job Dead-Letter / Retries Exhausted
**Symptoms**:
- Alert fired on `enermax_jobs_status_total{status="dead_letter"}`.
- User reports delayed or failed automated workflow action.

**Remediation Steps**:
1. Inspect dead-letter jobs:
   ```bash
   curl -H "Authorization: Bearer <ADMIN_TOKEN>" \
     "https://crm.enermaxsolar.com/api/v1/jobs?status=dead_letter"
   ```
2. Review `error_message` and `error_details` in the job payload.
3. Once the root cause (e.g. external supplier API outage, invalid parameter) is resolved, trigger manual re-queue:
   ```bash
   curl -X POST -H "Authorization: Bearer <ADMIN_TOKEN>" \
     "https://crm.enermaxsolar.com/api/v1/jobs/<JOB_ID>/retry"
   ```

---

### Playbook D: High Authentication Rate Limit Triggered (Brute Force Attack)
**Symptoms**:
- Alert on `enermax_rate_limit_hits_total{endpoint="/api/v1/auth/login"}`.
- HTTP 429 returned to attacker IP.

**Remediation Steps**:
1. Review IP in structured logs:
   ```bash
   grep 'RATE_LIMIT_EXCEEDED' /var/log/nginx/access.log
   ```
2. Ban attacker IP at the edge firewall or Cloudflare / Nginx level:
   ```bash
   iptables -A INPUT -s <ATTACKER_IP> -j DROP
   ```
