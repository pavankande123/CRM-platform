# Enermax CRM — Security Architecture & Threat Model

## 1. Security Overview

Security is a foundational design constraint of Enermax CRM. Because the platform will manage ₹5 crore+ of commercial operations, data leaks, cross-tenant breaches, and authentication flaws are treated as severe risks.

---

## 2. Core Security Controls

### 2.1 Multi-Tenant Isolation
* **Server-Side Enforcement**: Tenant resolution happens exclusively at the backend dependency injection layer (`get_current_tenant`, `get_current_user`).
* **Query Scoping**: Every database lookup, insertion, and update explicitly filters by `tenant_id == current_user.organization_id`.
* **Zero Trust Across Tenants**: Tenant A can never read, modify, or delete Tenant B's data, regardless of the API parameters supplied.

### 2.2 Authentication & Password Security
* **Argon2id Hashing**: Passwords are cryptographically salted and hashed using Argon2id (`time_cost=3`, `memory_cost=64MB`, `parallelism=4`). Legacy verification supports Bcrypt.
* **JWT Access & Refresh Tokens**:
  - Access tokens have short lifespans (15–60 minutes) and contain user UUID, tenant UUID, and assigned role.
  - Refresh tokens allow seamless renewal without storing passwords on the client.
  - Unique JWT IDs (`jti`) allow revocation tracking.

### 2.3 Role-Based Access Control (RBAC)
* Granular permission codes (e.g., `tenant:read`, `users:manage`, `audit:read`, `crm:read`, `crm:write`).
* Standard default roles: `admin` (super-admin access), `operator` (daily business operator), `viewer` (read-only).
* Endpoints declare required permissions via `Depends(require_permission("..."))`.

### 2.4 Audit Trail & Redaction
* An immutable `audit_logs` table records every critical event (LOGIN, REGISTER, LOGOUT, USER_CREATE, ORGANIZATION_UPDATE).
* The audit service runs automatic sanitization to redact passwords, secret tokens, and authorization headers from JSON metadata.

### 2.5 HTTP & Transport Security
* **Security Headers**: Injected via middleware on every response:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY` (clickjacking protection)
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: geolocation=(), camera=(), microphone=()`
* **CORS Restrictions**: Strict whitelist validation preventing unauthorized third-party origins from invoking endpoints.
* **SQL Injection Immunity**: 100% of queries use SQLAlchemy 2.0 parameterized expressions and ORM statements. No raw string interpolation is permitted.

---

## 3. Security Verification Checklist

| Security Check | Implemented & Verified |
| :--- | :---: |
| Tenant A cannot access Tenant B resources | YES (verified in `test_tenant_isolation.py`) |
| Passwords salted and hashed with Argon2id | YES (verified in `test_auth.py`) |
| Unauthenticated requests rejected with 401 | YES (verified in `test_auth.py`) |
| Unauthorized role actions rejected with 403 | YES (verified in `test_rbac.py`) |
| Passwords never leaked into audit metadata | YES (verified in `test_audit.py`) |
| Stack traces hidden from external clients | YES (verified in `test_error_handling.py`) |
| Request correlation tracking via `X-Request-ID`| YES (verified in `test_health.py`) |
