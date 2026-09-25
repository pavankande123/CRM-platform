# Enermax CRM — System Architecture (Phase 1 Foundation)

## 1. Executive Architectural Overview

Enermax CRM is engineered as a **modular monolith** optimized for high reliability, strict tenant isolation, and clear operational observability. The platform is designed to support Enermax's ₹5 crore business operations with an operator-driven workflow, while establishing an enterprise foundation capable of horizontally scaling to 30,000–40,000+ customer tenant organizations.

### High-Level Topology

```text
[ Browser / Client ]
        │
        │  HTTPS / JSON / Bearer JWT / X-Request-ID
        ▼
[ Edge Nginx / Ingress ]
        │
        ▼
[ FastAPI Application Core (Async) ]
  ├── RequestID & Latency Middleware
  ├── Security Headers Middleware
  ├── Global Exception Interceptors (RFC Error Envelopes)
  ├── Dependency Injection (DB Session, Tenant, User, RBAC)
  │
  ├── Auth & Tenant Service
  ├── Audit Service (Immutable Activity Stream)
  └── Health & Readiness Engine
        │
        ├── PostgreSQL 16 (Authoritative Source of Truth)
        │     ├── Organizations (Tenants)
        │     ├── Users & Roles & Permissions (RBAC)
        │     └── Audit Logs (Partitioned by Tenant)
        │
        └── Redis 7 (In-Memory Session & Cache Store)
```

---

## 2. Core Architectural Decisions

### 2.1 Modular Monolith vs Microservices
* **Decision**: Adopt a modular monolith rather than premature microservices.
* **Rationale**: Enermax operates with a lean team and a single-operator focus. Distributed microservices introduce operational friction (distributed tracing, network fallacies, split-brain transactions) without benefit at this stage. Internal modules (`auth`, `tenants`, `users`, `audit`) are decoupled via clean service interfaces, allowing future extraction into standalone microservices if load testing proves the necessity.

### 2.2 Relational Source of Truth (PostgreSQL)
* **Decision**: PostgreSQL is the single authoritative source of truth.
* **Rationale**: Financial data, customer records, and pipeline states require strict ACID compliance, transactional integrity, and referential constraints. Redis and search clusters serve as temporary caches or indexes only.

### 2.3 Strict Multi-Tenancy Boundary
* **Decision**: Tenant isolation is strictly enforced server-side on every request.
* **Rationale**: Relying on client-side filtering or single-attribute filtering is unsafe. Every authenticated request extracts the authenticated user and resolves the associated `organization_id`. Database queries programmatically filter by `tenant_id`.

---

## 3. Directory Layout & Module Structure

```text
enermax-crm/
├── backend/
│   ├── alembic/              # Database migration versions and config
│   ├── app/
│   │   ├── api/              # API routes and dependencies
│   │   │   ├── deps.py       # Dependency injection (Auth, Tenant, RBAC, DB)
│   │   │   └── v1/           # API v1 versioned endpoints
│   │   ├── core/             # Settings, Security, Logging, Error handling
│   │   ├── db/               # SQLAlchemy engine, session factory, base mixins
│   │   ├── middleware/       # Request-ID, Latency, Security headers
│   │   ├── models/           # Declarative database entities
│   │   ├── schemas/          # Pydantic validation contracts
│   │   └── services/         # Domain business logic (Auth, Audit, Tenant)
│   ├── tests/                # Pytest unit, API, RBAC, and isolation tests
│   ├── Dockerfile            # Multi-stage production container
│   ├── pyproject.toml        # Ruff and Pytest configuration
│   └── requirements.txt      # Pinned production Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/       # Common design system (Button, Card, Badge, etc.)
│   │   ├── context/          # Auth and Notification toast state
│   │   ├── pages/            # Login, Register, Dashboard, Audit, Users, Tenant
│   │   ├── services/         # API client with token auto-refresh and tracing
│   │   └── types/            # TypeScript data transfer models
│   ├── Dockerfile            # Multi-stage Nginx production container
│   ├── nginx.conf            # High-performance Nginx reverse proxy
│   └── vite.config.ts        # Vite + Tailwind v4 bundler
│
├── infrastructure/           # Deployment templates and scripts
├── scripts/                  # Development scripts (run_dev, run_tests, migrate_db)
├── docs/                     # Comprehensive architecture and operations documentation
├── .github/workflows/        # Automated CI/CD pipeline
├── docker-compose.yml        # Full-stack orchestrator
└── README.md                 # Primary developer landing page
```

---

## 4. Cross-Cutting Concerns

1. **Correlation & Tracing**: Every inbound HTTP request is assigned a unique `X-Request-ID`. This ID is tracked in Python `contextvars` and injected into every structured JSON log line.
2. **Standardized Error Handling**: Internal server errors return an error envelope with the `request_id`. Stack traces are strictly suppressed in non-development environments.
3. **Structured Logging**: Standard JSON output containing timestamp, level, service, request_id, tenant_id, and actor_id.
