# Enermax CRM — Environment Configuration Guide

## 1. Environment Lifecycle

The Enermax CRM architecture maintains strict separation between environments:

```text
[ LOCAL ] ──▶ [ DEVELOPMENT ] ──▶ [ STAGING ] ──▶ [ PRODUCTION ]
   │                 │                   │                 │
Local SQLite /   Dev RDS /           Staging RDS /     Multi-AZ RDS /
Local Redis      Dev Elasticache     Staging Cache     HA Redis /
                                                       Strict WAF
```

Never mix production keys, credentials, or databases with pre-production tiers.

---

## 2. Environment Variables Matrix

| Variable | Type | Default | Description | Production Requirement |
| :--- | :--- | :--- | :--- | :--- |
| `APP_NAME` | string | `Enermax CRM` | Application human-readable name | Standard string |
| `APP_ENV` | string | `development` | Deployment environment (`development`, `staging`, `production`) | Must be `production` |
| `DEBUG` | boolean | `false` | Enable verbose debugging and error output | Must be `false` |
| `LOG_LEVEL` | string | `INFO` | Logging threshold (`DEBUG`, `INFO`, `WARN`, `ERROR`) | `INFO` or `WARN` |
| `API_V1_PREFIX` | string | `/api/v1` | URL mount point for API v1 | Keep standard `/api/v1` |
| `SECRET_KEY` | string | — | Cryptographic secret for signing JWT tokens | High-entropy 64+ char random string |
| `ALGORITHM` | string | `HS256` | JWT signature algorithm | `HS256` or `RS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| int | `60` | Lifespan of access token | 15–60 minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | `7` | Lifespan of refresh token | 7–30 days |
| `CORS_ORIGINS` | JSON list | `["http://localhost:5173"]`| Whitelist of trusted frontend origins | Strict domain list (e.g. `https://crm.enermax.com`) |
| `POSTGRES_SERVER` | string | `localhost` | PostgreSQL host address | Managed RDS endpoint |
| `POSTGRES_PORT` | int | `5432` | PostgreSQL listening port | `5432` |
| `POSTGRES_USER` | string | `enermax_user` | Database master user | Dedicated IAM/Vault user |
| `POSTGRES_PASSWORD` | string | — | Database user password | Strong secret via Secrets Manager |
| `POSTGRES_DB` | string | `enermax_crm` | Primary database name | `enermax_crm_prod` |
| `DATABASE_URL` | string | — | Full async connection string | `postgresql+asyncpg://...` |
| `DB_POOL_SIZE` | int | `10` | SQLAlchemy connection pool size | 20–50 depending on worker count |
| `DB_MAX_OVERFLOW` | int | `20` | Max temporary connection overflow | 10–20 |
| `REDIS_URL` | string | `redis://localhost:6379/0` | Redis connection URL | TLS Redis URL `rediss://...` |

---

## 3. Secret Management Principles

1. **Zero Secret Commits**: The `.gitignore` file strictly excludes `.env`, `*.env`, and certificate files.
2. **Secret Rotation**: `SECRET_KEY` and database passwords must be stored in a cloud secret manager (AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault) and injected into container environments at startup.
3. **Audit Redaction**: The system automatically redacts sensitive keywords (`password`, `secret`, `token`, `key`) from audit logs and application traces.
