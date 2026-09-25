# Enermax CRM — Testing & Quality Assurance Guide

## 1. Testing Philosophy

Enermax CRM manages business-critical operations. Unverified features and superficial unit tests are strictly unacceptable.

Every phase requires automated test coverage proving:
1. Operational readiness (health & liveness probes)
2. Authentication & session security
3. Multi-tenant isolation (strict boundaries)
4. Granular RBAC authorization
5. Audit trail generation and sensitive field redaction
6. Standardized error envelopes and correlation IDs

---

## 2. Test Suite Breakdown

### 2.1 Backend Tests (`backend/tests/`)
All backend tests execute asynchronously against an in-memory SQLite database utilizing SQLAlchemy 2.0 async engine and `httpx.AsyncClient`.

| Test File | Test Case | Target Verification |
| :--- | :--- | :--- |
| `test_health.py` | `test_liveness_probe` | Probes `/health` returning 200 OK and version info |
| `test_health.py` | `test_readiness_probe` | Validates `/ready` dependency status and latency |
| `test_auth.py` | `test_register_and_login_flow` | Tests registration, password verification, tokens, `/me`, and logout |
| `test_auth.py` | `test_unauthenticated_request_rejected` | Proves protected routes reject missing tokens with 401 |
| `test_tenant_isolation.py` | `test_strict_tenant_isolation` | **Mandatory Test**: Proves Tenant B cannot view or modify Tenant A's users, organizations, or audit logs |
| `test_audit.py` | `test_audit_logging_and_sanitization` | Proves audit log generation and confirms passwords are never stored |
| `test_audit.py` | `test_audit_pagination` | Verifies paginated retrieval of audit records |
| `test_rbac.py` | `test_rbac_permission_enforcement` | Proves operator role has restricted access compared to admin |
| `test_error_handling.py` | `test_standard_error_envelope_on_validation_failure` | Verifies 422 input validation returns standard RFC envelope with `X-Request-ID` |
| `test_error_handling.py` | `test_standard_error_envelope_on_not_found` | Verifies 404 behavior and header correlation |

---

## 3. Running the Test Suite

### Run All Tests via Script
```powershell
.\scripts\run_tests.ps1
```

### Run Backend Tests Exclusively
```bash
backend\.venv\Scripts\pytest.exe backend/tests -v
```

### Run Frontend Typecheck and Build Validation
```bash
cd frontend
npm run build
```
