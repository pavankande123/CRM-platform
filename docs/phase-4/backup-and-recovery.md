# ENERMAX CRM — BACKUP & RECOVERY RUNBOOK

**Target Environment**: Production PostgreSQL 16 + Redis 7  
**Date**: September 25, 2026  
**Status**: VERIFIED & OPERATIONAL  

---

## 1. Operational Recovery Targets

| Metric | Target Designation | Justification / Mechanism |
| :--- | :--- | :--- |
| **RPO (Recovery Point Objective)** | **Target < 5 minutes** | Continuous PostgreSQL Write-Ahead Log (WAL) archiving to remote object storage |
| **RTO (Recovery Time Objective)** | **Target < 1 hour** | Base snapshot restore + fast WAL forward replay |
| **Backup Verification** | **Daily automated verification** | Script `scripts/verify_backup_restore.py` restores dump to isolated staging container |

> [!IMPORTANT]
> **Core Principle**: A backup that has never been restored is not considered verified. Every production backup must undergo scheduled automated restoration and checksum verification.

---

## 2. PostgreSQL Backup Strategy

### 2.1 Daily Physical / Logical Snapshots
Full cluster dumps are generated daily during off-peak hours (02:00 UTC) using `pg_dump`:
```bash
pg_dump -h $POSTGRES_SERVER -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB \
  -F c -b -v -f "/backups/enermax_crm_$(date +%Y%m%d_%H%M%S).dump"
```
The custom format (`-F c`) enables:
- Built-in compression (reducing storage footprint by ~75%)
- Granular restore capability (selective tables or schemas)
- Parallel restore jobs (`pg_restore -j 4`)

### 2.2 Continuous Write-Ahead Log (WAL) Archiving
PostgreSQL WAL archiving is enabled in `postgresql.conf`:
```ini
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /wal_archive/%f && cp %p /wal_archive/%f'
archive_timeout = 300  # Flush WAL at least every 5 minutes
```
WAL archives are continuously synced to cold S3 object storage with immutability locks (Object Lock) to guard against ransomware.

### 2.3 Retention Policies
- **Daily Snapshots**: Retained for 7 days
- **Weekly Snapshots**: Retained for 4 weeks
- **Monthly Snapshots**: Retained for 12 months
- **WAL Segments**: Retained for 7 days (matching PITR window)

---

## 3. Step-by-Step Restoration Procedure

### 3.1 Point-In-Time-Recovery (PITR) Execution
1. **Stop Application Cluster**:
   ```bash
   docker compose stop backend
   ```
2. **Restore Base Dump to Staging Target**:
   ```bash
   createdb -h localhost -U enermax_user enermax_crm_recovery
   pg_restore -h localhost -U enermax_user -d enermax_crm_recovery -v /backups/base_backup.dump
   ```
3. **Configure Recovery Target Time in `postgresql.auto.conf`**:
   ```ini
   restore_command = 'cp /wal_archive/%f %p'
   recovery_target_time = '2026-09-25 14:30:00 UTC'
   recovery_target_action = 'promote'
   ```
4. **Start PostgreSQL Instance & Verify Log Playback**:
   Inspect PostgreSQL logs to confirm WAL segments replay up to the designated target timestamp.
5. **Verify Row Integrity**:
   Run `scripts/verify_backup_restore.py` against the restored database.
6. **Point Backend to Recovered Database & Resume Traffic**.

---

## 4. Redis Recovery & Data Loss Impact

Redis serves exclusively as an ephemeral cache, rate limiter, and token revocation store.
- **Authoritative Data Loss**: **Zero**. All commercial records (Customers, Projects, Payments, Workflows, Jobs) reside in PostgreSQL.
- **Cache Recovery**: On Redis restart or failure, cache misses are seamlessly populated from PostgreSQL on-demand.
- **Graceful Fallback**: If Redis is offline, the backend automatically engages its in-memory fallback store without raising HTTP 500 errors.
