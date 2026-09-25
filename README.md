# Enermax CRM — Enterprise SaaS Platform

> **Proprietary, production-grade SaaS CRM platform engineered for Enermax.**  
> Built strictly phase-by-phase with enterprise engineering standards underneath a simple, operator-friendly surface.

[![CI Pipeline](https://github.com/enermax/crm/actions/workflows/ci.yml/badge.svg)](https://github.com/enermax/crm/actions)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-blue.svg)](LICENSE)
[![Phase](https://img.shields.io/badge/Phase-1%20Foundation%20Verified-emerald.svg)](#phase-1-status)

---

## 1. Project Mission & Business Context

Enermax handles approximately **₹5 crore of business** in renewable energy systems. The legacy CRM suffered from excessive navigation complexity, unnecessary features, rigid pipelines, poor reporting, and an architecture that assumed multi-person handoffs when operations are predominantly driven by a **single operator**.

### Core Product Mandate:
> **SIMPLE OPERATION + CLEAR INFORMATION + FLEXIBLE PROCESS + RELIABLE DATA**

Underneath this simple surface lies an enterprise-grade platform supporting:
* Strict Multi-Tenancy Boundary
* Scalability up to 30,000–40,000+ Tenant Organizations
* Comprehensive Audit Trail
* Robust Role-Based Access Control (RBAC)
* High Reliability and Zero Data Corruption

---

## 2. Technology Stack

* **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons
* **Backend**: Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic
* **Database**: PostgreSQL 16 (Authoritative Source of Truth)
* **Cache & Session**: Redis 7
* **Containerization**: Docker & Docker Compose (Multi-stage builds)
* **Testing**: Pytest, AsyncIO, HTTPX, TypeScript Compiler

---

## 3. Quickstart (Local Development)

### Option 1: Docker Compose (All Services)
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Launch stack
docker compose up --build
```
* Frontend: [http://localhost:5173](http://localhost:5173)
* Backend API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
* Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### Option 2: Native Development
See detailed instructions in [Development Guide](docs/development.md).

```powershell
# Windows automated test runner
.\scripts\run_tests.ps1
```

---

## 4. Repository Structure

```text
enermax-crm/
├── backend/                  # FastAPI modular monolith application
│   ├── alembic/              # Database migration schemas
│   ├── app/                  # Application source code (api, core, db, models, schemas, services)
│   ├── tests/                # Automated test suite (health, auth, tenant isolation, audit, rbac)
│   └── Dockerfile            # Multi-stage production container
├── frontend/                 # React + TypeScript + Vite + Tailwind client
│   ├── src/                  # Components, contexts, pages, services, types
│   ├── nginx.conf            # High-performance static web server config
│   └── Dockerfile            # Multi-stage Nginx production container
├── infrastructure/           # Cloud deployment manifests
├── scripts/                  # Developer utilities (run_dev, run_tests, migrate_db)
├── docs/                     # Engineering documentation
│   ├── architecture.md       # Topology and architectural rationale
│   ├── development.md        # Local environment and workflows
│   ├── environment.md        # Environment variables and secrets
│   ├── database.md           # Schema, migrations, and connection pooling
│   ├── security.md           # Threat model, isolation guarantees, and RBAC
│   ├── testing.md            # Test breakdown and execution
│   ├── deployment.md         # Staging/production deployment and rollbacks
│   └── phase_1_verification.md # Formal Phase 1 Verification Report
├── .github/workflows/ci.yml  # Automated CI pipeline
├── docker-compose.yml        # Orchestration configuration
├── .env.example              # Documented environment variables template
└── README.md                 # Primary overview
```

---

## 5. Phase 1 Status & Definition of Done

All 20 sub-phases of **Phase 1 (Production Foundation)** have been implemented, automated, and verified:
* [x] **Phase 1.1** Clean repository architecture established
* [x] **Phase 1.2** Frontend foundation with design system, AppShell, and error boundaries
* [x] **Phase 1.3** FastAPI backend with API versioning (`/api/v1`) and dependency injection
* [x] **Phase 1.4** PostgreSQL async database foundation, connection pooling, and Alembic migrations
* [x] **Phase 1.5** Authentication with Argon2id password hashing and JWT access/refresh tokens
* [x] **Phase 1.6** Authorization foundation with RBAC (Organizations, Users, Roles, Permissions)
* [x] **Phase 1.7** Strict Tenant Isolation with server-side enforcement and automated tests
* [x] **Phase 1.8** Immutable Audit Trail with automatic sensitive field redaction
* [x] **Phase 1.9** Standardized RFC error envelopes with correlation Request IDs
* [x] **Phase 1.10** Structured JSON logging with request, tenant, and user context
* [x] **Phase 1.11** Health and Readiness probes (`/health`, `/ready`)
* [x] **Phase 1.12** Production multi-stage Dockerfiles and docker-compose
* [x] **Phase 1.13** Documented local development workflows and scripts
* [x] **Phase 1.14** Comprehensive test suite (100% pass rate)
* [x] **Phase 1.15** CI/CD pipeline definition (`.github/workflows/ci.yml`)
* [x] **Phase 1.16** Complete documentation suite (`docs/`)
* [x] **Phase 1.17** Code quality and static typing enforcement
* [x] **Phase 1.18** Latency tracking middleware (`X-Response-Time`)
* [x] **Phase 1.19** Security review completed with zero high/critical issues
* [x] **Phase 1.20** Final verification report produced

*Strict Scope Boundary*: Phase 2 business modules (Customer management, Pipeline deals, Payment tracking, AI assistant) were intentionally not implemented in Phase 1 to guarantee a rock-solid foundation.
