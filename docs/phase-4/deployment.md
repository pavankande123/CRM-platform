# ENERMAX CRM — PHASE 4 DEPLOYMENT ARCHITECTURE

**Target**: Reproducible SaaS Deployment Topology  
**Date**: September 25, 2026  
**Status**: SPECIFIED & DOCKER-VERIFIED  

---

## 1. Architecture Topology & Design Rationale

Enermax employs a **Hardened Modular Monolith** deployment model:

```
[Internet Traffic]
       │
       ▼ (Port 443 / 80)
[Nginx Reverse Proxy & Static File Server] (docker/nginx.conf)
       │
       ├───► /               ───► Static SPA Bundle (React 18 / Vite dist/)
       ├───► /api/           ───► FastAPI Backend Cluster (Gunicorn / Uvicorn)
       └───► /health|metrics ───► Direct backend probes
                                        │
                       ┌────────────────┴────────────────┐
                       ▼                                 ▼
             [PostgreSQL 16 Primary]           [Redis 7 Cache Cluster]
             (Authoritative Database)          (Session, RateLimit, Cache)
```

### Why Kubernetes is Not Introduced in Phase 4
As mandated by the Phase 4 constraints:
> "DO NOT add infrastructure merely to appear enterprise-grade. Every dependency must have a documented reason."

- **Current Stage**: The Enermax application is a stateless modular monolith with background workers. A Docker Compose or containerized VM setup (AWS ECS / GCP Cloud Run / Docker Swarm / Hetzner Dedicated + Docker Compose) comfortably handles tens of thousands of requests per second across multiple container instances with sub-second failover.
- **Operational Complexity**: Kubernetes introduces control-plane etcd maintenance, CNI networking overhead, ingress controller maintenance, and Helm chart drift without offering any scaling benefit that horizontal container scaling cannot achieve at this phase.
- **Decision**: Deferred to a future phase if and when microservice decoupling or multi-region active-active database clustering becomes a strict business requirement.

---

## 2. Docker Compose Deployment

The primary deployment is orchestrated via `docker-compose.yml`:

### Services
1. **`postgres`**: `postgres:16-alpine`
   - Persistent volume: `postgres_data`
   - Internal network only
   - Strict healthcheck using `pg_isready`
2. **`redis`**: `redis:7-alpine`
   - Persistent volume: `redis_data`
   - Healthcheck using `redis-cli ping`
3. **`backend`**: FastAPI backend
   - Multi-worker Uvicorn (`--workers 4`)
   - Auto-migrates database on container startup (`alembic upgrade head`)
   - Dependent on `postgres` and `redis` being healthy
4. **`frontend`**: React 18 production bundle
   - Multi-stage build producing static HTML/JS/CSS assets served via Nginx.

---

## 3. Production Deployment Commands

### Step 1: Prepare Environment Secrets
```bash
cp .env.production.example .env.production
# Generate secure 64-character secret key
openssl rand -hex 32
# Populate production credentials in .env.production
```

### Step 2: Build and Launch Containers
```bash
docker compose -f docker-compose.yml --env-file .env.production up -d --build
```

### Step 3: Verify Deployment Health
```bash
# 1. Check container statuses
docker compose ps

# 2. Check application readiness probe
curl -I http://localhost:8000/ready
# Expected: HTTP/1.1 200 OK

# 3. Check Prometheus metrics
curl -s http://localhost:8000/metrics | grep enermax_http_requests_total
```
