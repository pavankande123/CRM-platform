# ENERMAX CRM — PHASE 4 ARCHITECTURE SPECIFICATION

## SaaS Scale & Production Hardening

---

### 1. Executive Summary

Phases 1, 2, and 3 delivered a configurable, multi-tenant modular monolith CRM covering:
- Operator workflows, Customers, Contacts, Projects, Flexible Pipelines, Follow-ups, Payments, Notes, Documents, and Executive Dashboard.
- Configurable Pipeline stages, Metadata-driven Custom Fields, Saved Views, Declarative Workflow Engine, In-App Notifications, and Approval Governance.

**Phase 4 Objective**: Transform Enermax from a functional configurable CRM into a hardened, observable, scalable SaaS platform capable of sustaining high multi-tenant loads with measurable evidence, robust security, durable background execution, operational resilience, and automated disaster recovery.

---

### 2. High-Level Architecture Topology

```
+---------------------------------------------------------------------------------------------------+
|                                      EDGE & REVERSE PROXY                                         |
|  - TLS Termination (Let's Encrypt / Cloudflare)                                                   |
|  - Nginx Reverse Proxy (Static Asset Caching, Gzip/Brotli, Request Rate Limiting)                |
|  - Security Headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)                           |
+------------------------------------+--------------------------------------------------------------+
                                     |
              +----------------------+----------------------+
              |                                             |
+-------------v----------------------+       +--------------v---------------------------------------+
|    CLIENT LAYER (React 18 SPA)     |       |            FASTAPI BACKEND CLUSTER                   |
| - Vite Production Bundle (425 KB)  |       | - Gunicorn / Uvicorn Multi-Worker Processes         |
| - Auto Token Refresh (Queue-Safe)  |       | - Request ID & Correlation Tracking Middleware       |
| - Tenant Context Injection         |       | - IP & Tenant Rate Limiting (Redis / Fallback)       |
| - Responsive Operator UI           |       | - Structured JSON Logging & Credential Scrubbing     |
+------------------------------------+       | - Prometheus Metrics Endpoint (/metrics)             |
                                             | - RBAC & Strict Tenant Isolation Guard               |
                                             | - OpenTelemetry Context Propagation                  |
                                             +----------------------+-------------------------------+
                                                                    |
               +----------------------------------------------------+-----------------------------------------------+
               |                                                    |                                               |
+--------------v-------------------------------+   +----------------v-------------------------------+   +-----------v-----------------------+
|      POSTGRESQL 16 (AUTHORITATIVE STORE)     |   |          REDIS 7 (DISTRIBUTED CACHE)           |   |       OBJECT STORAGE ENGINE       |
| - Row-Level Tenant Isolation (tenant_id)     |   | - Connection Pooling (asyncio)                 |   | - Interface: StorageBackend       |
| - Multi-Column Tenant Indexes                |   | - Namespaces: cache, session, ratelimit, jobs  |   | - LocalDisk (Dev/Test)            |
| - Connection Pooling (size=20, overflow=10)  |   | - Strict TTL on all keys                       |   | - S3 / MinIO (Production)         |
| - Statement Timeout (15s query guard)        |   | - Graceful Circuit Breaker Failure Degradation |   | - MIME & 25MB Size Validation     |
| - PgBouncer for High Tenant Connection Multiplexing | +--------------------------------------------+   +-----------------------------------+
+--------------+-------------------------------+
               |
+--------------v------------------------------------------------------------------------------------+
|                                    DURABLE BACKGROUND JOB SUBSYSTEM                               |
| - Durable Job Model in PostgreSQL (queued, running, completed, failed, retrying, dead_letter)      |
| - Asynchronous JobWorker with Exponential Backoff & Max Retries                                   |
| - Strict Idempotency Hash Deduplication                                                           |
| - Correlation ID & Tenant Context Preservation                                                    |
+---------------------------------------------------------------------------------------------------+
```

---

### 3. Tenancy & Scaling Model

#### 3.1 Shared Database with Row-Level Partitioning (`tenant_id`)
Enermax employs a **shared database, shared schema** tenancy model. Every tenant-scoped entity contains a mandatory `tenant_id` foreign key mapped to `organizations.id` with `ondelete="CASCADE"`.

**Rationale for 30k–40k Customer Organizations**:
- Separate databases or schemas per tenant at 40,000 tenants creates severe connection pool exhaustion, file descriptor limits, and catastrophic migration management overhead.
- Shared schema with compound indexing (`tenant_id`, `created_at` / `status` / `entity_id`) allows PostgreSQL B-tree indexes to provide sub-millisecond seek times for any single tenant regardless of global tenant count.
- In production, **PgBouncer** is placed between the FastAPI workers and PostgreSQL in transaction pooling mode, enabling thousands of client connections to share 50–100 physical database connections.

---

### 4. Database Hardening & Indexing Strategy

1. **Connection Pool Configuration**:
   - `pool_size`: 20 connections per backend process.
   - `max_overflow`: 10 burst connections.
   - `pool_timeout`: 30 seconds wait before raising timeout.
   - `pool_recycle`: 1800 seconds (30 minutes) to eliminate stale connections.
   - `pool_pre_ping`: `True` to detect dropped sockets prior to query execution.
2. **Statement & Lock Timeouts**:
   - `statement_timeout = 15000` (15 seconds) to prevent runaway or poorly tuned queries from holding table locks.
   - `idle_in_transaction_session_timeout = 30000` (30 seconds) to terminate hung transactions.
3. **Compound Tenant Indexes**:
   - `customers`: `(tenant_id, is_active)`, `(tenant_id, created_at)`
   - `projects`: `(tenant_id, stage_id)`, `(tenant_id, customer_id)`, `(tenant_id, status)`
   - `follow_ups`: `(tenant_id, status, due_date)`
   - `payments`: `(tenant_id, status, payment_date)`
   - `notifications`: `(tenant_id, user_id, is_read)`
   - `approvals`: `(tenant_id, status)`
   - `workflow_executions`: `(tenant_id, workflow_id, status)`
   - `audit_logs`: `(tenant_id, created_at)`
   - `jobs`: `(tenant_id, status, scheduled_at)`

---

### 5. Redis Hardening & Resiliency

1. **Strict Namespaces**:
   - Cache: `enermax:cache:{tenant_id}:{entity}:{key}`
   - Rate Limits: `enermax:ratelimit:{scope}:{identifier}`
   - Revocations: `enermax:revocation:{jti}`
   - Job State: `enermax:job:{tenant_id}:{job_id}`
2. **TTL Mandate**: Every key written to Redis must specify an explicit TTL. No unbounded keys are permitted.
3. **Safe Failure / Circuit Breaker**:
   - If Redis connection times out or fails, operations degrade gracefully:
     - Rate limiter defaults to in-memory sliding window.
     - Cache bypasses directly to PostgreSQL.
     - Token revocation falls back to in-memory/DB store.
     - System remains available without throwing HTTP 500 errors.

---

### 6. Background Job Architecture

1. **Durable Database Job Entity**:
   - Every background task is recorded in the `jobs` table before execution.
   - Tracks: `id`, `tenant_id`, `queue`, `job_type`, `payload`, `status`, `retry_count`, `max_retries`, `retry_backoff_seconds`, `scheduled_at`, `started_at`, `completed_at`, `error_message`, `error_details`, `idempotency_key`, `correlation_id`.
2. **State Machine**:
   - `queued` -> `running` -> `completed`
   - `running` -> `retrying` (when retry_count < max_retries with exponential backoff)
   - `retrying` -> `running`
   - `running` -> `dead_letter` / `failed` (when retries exhausted)
3. **Pluggable Architecture**:
   - `JobService` provides standard `enqueue()`, `get_status()`, `retry()` methods.
   - Default runner runs asynchronous workers inside the FastAPI event loop without blocking API requests; can be pointed to a distributed worker fleet without modifying business services.

---

### 7. Rate Limiting & Abuse Protection

1. **Unauthenticated Endpoints** (`/api/v1/auth/login`, `/api/v1/auth/register`):
   - Sliding window rate limit: 10 requests / minute per client IP.
   - Protects against brute-force password guessing and credential stuffing.
2. **Authenticated API Traffic**:
   - Per-tenant / per-user limit: 300 requests / minute.
   - Prevents noisy neighbors or rogue automated scripts from degrading shared SaaS resources.
3. **Response Protocol**:
   - Exceeded limits return HTTP 429 `Too Many Requests`.
   - Headers: `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
   - Body: Standard Enermax error envelope (`code: "RATE_LIMIT_EXCEEDED"`).

---

### 8. Observability & Operational Diagnostics

1. **Structured JSON Logging**:
   - Emits machine-readable JSON logs for ingestion by Grafana Loki, Datadog, or CloudWatch.
   - Attributes: `timestamp`, `level`, `request_id`, `correlation_id`, `tenant_id`, `user_id`, `endpoint`, `latency_ms`, `status_code`.
   - **Credential Scrubbing**: Interceptor automatically scrubs passwords, bearer tokens, cookies, and secret keys.
2. **Application Metrics (`/metrics`)**:
   - Prometheus text format exposed for monitoring:
     - `http_requests_total`
     - `http_request_duration_seconds`
     - `db_pool_connections_active`, `db_pool_connections_idle`
     - `jobs_status_total`
     - `workflow_executions_total`
     - `rate_limit_hits_total`
3. **Tracing Evaluation (OpenTelemetry)**:
   - Evaluated for high-scale tracing. Request ID and correlation IDs injected across all HTTP requests, database transactions, background jobs, and audit logs.

---

### 9. Security Hardening

1. **Authentication**:
   - Argon2id / Bcrypt password hashing.
   - Access tokens (60 min expiry) and Refresh tokens (7 days expiry).
   - **Refresh Token Rotation**: Refreshing generates a new token pair and invalidates the previous refresh token.
   - **Logout Revocation**: Logout actively revokes the active token JTI in the revocation store.
2. **Authorization & RBAC**:
   - Scoped roles (`admin`, `operator`, `viewer`) and fine-grained permissions.
3. **HTTP Security**:
   - Strict security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`).
   - Request body limit middleware (10 MB standard, 25 MB documents).

---

### 10. File Storage Foundation

1. **Storage Abstraction (`StorageBackend`)**:
   - Decouples business logic from physical storage medium.
   - `LocalStorageBackend`: Files stored under `storage/{tenant_id}/{year}/{month}/{uuid}.{ext}`. Path traversal protected via realpath resolution.
   - `S3StorageBackend`: Compatible with AWS S3, MinIO, or Cloudflare R2 using standard S3 API and presigned URLs.
2. **Validation**:
   - Whitelist of allowed MIME types (PDF, images, spreadsheets, text).
   - Enforced 25MB maximum size.
   - Database stores only document metadata.

---

### 11. Backup & Recovery Strategy

1. **PostgreSQL**:
   - Daily full database dumps (`pg_dump -Fc`).
   - Write-Ahead Log (WAL) archiving for continuous Point-in-Time Recovery (PITR).
   - Verification script: `scripts/verify_backup_restore.py` creates a temporary database, restores the dump, and validates record integrity.
2. **Operational Recovery Targets**:
   - **RTO (Recovery Time Objective)**: Target < 1 hour.
   - **RPO (Recovery Point Objective)**: Target < 5 minutes (via continuous WAL archiving).
3. **Redis**: In-memory ephemeral cache/rate-limit store; failure is non-fatal.
