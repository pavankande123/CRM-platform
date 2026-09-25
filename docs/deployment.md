# Enermax CRM — Deployment & Operations Guide

## 1. Overview

The platform uses containerization to ensure consistent, repeatable deployments across development, staging, and production environments.

---

## 2. Containerized Production Deployment

### 2.1 Building Docker Images

```bash
# Build backend image
docker build -t enermax-crm-backend:v0.1.0 ./backend

# Build frontend image
docker build -t enermax-crm-frontend:v0.1.0 ./frontend
```

### 2.2 Running with Docker Compose (Production Profile)

```bash
# 1. Create production environment file with secure secrets
cp .env.example .env.production
# (Fill in actual production credentials)

# 2. Launch production stack
docker compose --env-file .env.production up -d
```

---

## 3. Database Migration Procedures

Before cutting over traffic to new application instances, run the database migrations:

```bash
# Inside the backend container or via standalone runner:
docker compose exec backend alembic upgrade head
```

---

## 4. Rollback Strategy

1. **Application Rollback**: If a deployment encounters errors, revert container image tags to the previous stable release:
   ```bash
   docker service update --image enermax-crm-backend:v0.0.9 enermax_backend
   ```
2. **Database Rollback**: If a schema migration caused regressions:
   ```bash
   docker compose exec backend alembic downgrade -1
   ```

---

## 5. Log Inspection & Monitoring

* **Application Logs**: Backend outputs structured JSON logs to stdout:
  ```bash
  docker compose logs -f --tail=100 backend
  ```
* **Filter by Request ID**:
  ```bash
  docker compose logs backend | grep "req_abc123"
  ```
* **Filter by Tenant ID**:
  ```bash
  docker compose logs backend | grep "tenant_id"
  ```

---

## 6. Backup and Restore Procedures

### 6.1 Database Backup (PostgreSQL)
```bash
# Automated daily snapshot
docker compose exec -T postgres pg_dump -U enermax_user -d enermax_crm | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 6.2 Database Restore
```bash
# Decompress and restore from backup file
gunzip -c backup_20260925_100000.sql.gz | docker compose exec -T postgres psql -U enermax_user -d enermax_crm
```
