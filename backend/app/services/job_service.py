import datetime
import logging
import traceback
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.logging import request_id_ctx
from app.models.job import Job

logger = logging.getLogger("enermax.jobs")

# Type alias for async job handler functions: async def handler(payload: dict, tenant_id: uuid.UUID, db: AsyncSession) -> dict
JobHandler = Callable[[Dict[str, Any], uuid.UUID, AsyncSession], Coroutine[Any, Any, Dict[str, Any]]]

# Global registry of job handlers by job_type
_JOB_HANDLERS: Dict[str, JobHandler] = {}


def register_job_handler(job_type: str, handler: JobHandler) -> None:
    """Register an asynchronous worker handler for a specific job_type."""
    clean_type = job_type.strip().lower()
    _JOB_HANDLERS[clean_type] = handler
    logger.debug(f"Registered job handler for '{clean_type}'")


# ---------------------------------------------------------------------------
# Default Handlers
# ---------------------------------------------------------------------------
async def _handle_test_echo(payload: Dict[str, Any], tenant_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    """Test handler for verifying background worker execution."""
    if payload.get("simulate_error"):
        raise RuntimeError(payload.get("error_message", "Simulated job failure"))
    return {"status": "ok", "received": payload, "tenant_id": str(tenant_id)}


register_job_handler("test.echo", _handle_test_echo)


# ---------------------------------------------------------------------------
# Job Management & Enqueuing
# ---------------------------------------------------------------------------
async def enqueue_job(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    job_type: str,
    payload: Dict[str, Any],
    queue: str = "default",
    max_retries: int = 3,
    retry_backoff_seconds: int = 5,
    scheduled_at: Optional[datetime.datetime] = None,
    idempotency_key: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> Job:
    """
    Enqueues a durable background job.
    Guarantees tenant isolation, idempotency deduplication, and scheduling parameters.
    """
    clean_type = job_type.strip().lower()
    now = datetime.datetime.now(datetime.timezone.utc)
    target_sched = scheduled_at or now
    cid = correlation_id or request_id_ctx.get()

    # Idempotency check if key provided
    if idempotency_key:
        stmt = select(Job).where(
            Job.tenant_id == tenant_id,
            Job.idempotency_key == idempotency_key,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            if existing.status in ("queued", "running", "completed"):
                logger.info(
                    f"Duplicate background job skipped: key={idempotency_key}, status={existing.status}"
                )
                return existing
            elif existing.status in ("failed", "dead_letter"):
                # Re-queue previously failed job with same idempotency key
                existing.status = "queued"
                existing.retry_count = 0
                existing.scheduled_at = target_sched
                existing.payload = payload
                existing.error_message = None
                existing.error_details = None
                await db.commit()
                await db.refresh(existing)
                return existing

    job = Job(
        tenant_id=tenant_id,
        queue=queue.strip().lower(),
        job_type=clean_type,
        payload=payload,
        status="queued",
        retry_count=0,
        max_retries=max_retries,
        retry_backoff_seconds=retry_backoff_seconds,
        scheduled_at=target_sched,
        idempotency_key=idempotency_key,
        correlation_id=cid,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    logger.info(
        f"Enqueued background job {job.id} [{clean_type}] in queue '{queue}' for tenant {tenant_id}",
        extra={"job_id": str(job.id), "job_type": clean_type, "tenant_id": str(tenant_id)},
    )
    return job


async def get_job(db: AsyncSession, tenant_id: uuid.UUID, job_id: uuid.UUID) -> Job:
    """Retrieve job details with strict tenant isolation."""
    stmt = select(Job).where(Job.id == job_id, Job.tenant_id == tenant_id)
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise NotFoundError(message="Background job not found.")
    return job


async def list_jobs(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    status: Optional[str] = None,
    queue: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Job], int]:
    """Retrieve paginated list of background jobs for a tenant."""
    query = select(Job).where(Job.tenant_id == tenant_id)
    count_query = select(func.count(Job.id)).where(Job.tenant_id == tenant_id)

    if status:
        query = query.where(Job.status == status.strip().lower())
        count_query = count_query.where(Job.status == status.strip().lower())
    if queue:
        query = query.where(Job.queue == queue.strip().lower())
        count_query = count_query.where(Job.queue == queue.strip().lower())
    if job_type:
        query = query.where(Job.job_type == job_type.strip().lower())
        count_query = count_query.where(Job.job_type == job_type.strip().lower())

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Job.created_at.desc()).offset(offset).limit(limit)
    jobs = (await db.execute(query)).scalars().all()

    return list(jobs), total


async def retry_job(db: AsyncSession, tenant_id: uuid.UUID, job_id: uuid.UUID) -> Job:
    """Manually resets a failed or dead-letter job to queued status."""
    job = await get_job(db, tenant_id, job_id)
    if job.status == "completed":
        raise ValidationError(message="Cannot retry a job that has already completed successfully.")

    job.status = "queued"
    job.retry_count = 0
    job.scheduled_at = datetime.datetime.now(datetime.timezone.utc)
    job.started_at = None
    job.completed_at = None
    job.error_message = None
    job.error_details = None
    await db.commit()
    await db.refresh(job)
    return job


# ---------------------------------------------------------------------------
# Background Worker Execution Runner
# ---------------------------------------------------------------------------
async def execute_job(db: AsyncSession, job: Job) -> bool:
    """
    Executes a single job with transactional state transitions,
    exponential backoff retry scheduling, and dead-letter handling.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    job.status = "running"
    job.started_at = now
    await db.commit()

    handler = _JOB_HANDLERS.get(job.job_type)
    if not handler:
        job.status = "failed"
        job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        job.error_message = f"No registered handler for job type '{job.job_type}'"
        await db.commit()
        return False

    try:
        result = await handler(job.payload, job.tenant_id, db)
        job.status = "completed"
        job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        job.result_data = result
        job.error_message = None
        job.error_details = None
        await db.commit()
        return True

    except Exception as exc:
        err_msg = str(exc)
        err_trace = traceback.format_exc()
        logger.error(
            f"Job {job.id} failed execution: {err_msg}",
            extra={"job_id": str(job.id), "error": err_msg},
        )
        job.retry_count += 1

        if job.retry_count <= job.max_retries:
            # Exponential backoff calculation
            backoff_sec = job.retry_backoff_seconds * (2 ** (job.retry_count - 1))
            job.status = "retrying"
            job.scheduled_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=backoff_sec)
            job.error_message = f"Retry {job.retry_count}/{job.max_retries}: {err_msg}"
            job.error_details = {"traceback": err_trace, "backoff_seconds": backoff_sec}
        else:
            # Max retries exhausted -> Move to dead_letter
            job.status = "dead_letter"
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            job.error_message = f"Max retries exhausted ({job.max_retries}): {err_msg}"
            job.error_details = {"traceback": err_trace}

        await db.commit()
        return False
