import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.job import JobCreate, JobRead, JobRetryResponse
from app.services import job_service

router = APIRouter()


@router.post("", response_model=StandardResponse[JobRead], status_code=status.HTTP_201_CREATED, summary="Enqueue Background Job")
async def enqueue_job(
    data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[JobRead]:
    """Enqueues a durable background job for the active tenant organization."""
    job = await job_service.enqueue_job(
        db=db,
        tenant_id=current_user.organization_id,
        job_type=data.job_type,
        payload=data.payload,
        queue=data.queue,
        max_retries=data.max_retries,
        retry_backoff_seconds=data.retry_backoff_seconds,
        scheduled_at=data.scheduled_at,
        idempotency_key=data.idempotency_key,
        correlation_id=data.correlation_id,
    )
    return StandardResponse(data=JobRead.model_validate(job), message="Job enqueued successfully")


@router.get("", response_model=StandardResponse[List[JobRead]], summary="List Tenant Background Jobs")
async def list_jobs(
    status_filter: Optional[str] = Query(None, alias="status"),
    queue: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[JobRead]]:
    """List background jobs for the active tenant with optional status, queue, or type filtering."""
    jobs, total = await job_service.list_jobs(
        db=db,
        tenant_id=current_user.organization_id,
        status=status_filter,
        queue=queue,
        job_type=job_type,
        limit=limit,
        offset=offset,
    )
    return StandardResponse(
        data=[JobRead.model_validate(j) for j in jobs],
        message=f"Retrieved {len(jobs)} background jobs (total {total})",
    )


@router.get("/{id}", response_model=StandardResponse[JobRead], summary="Get Background Job Details")
async def get_job(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[JobRead]:
    """Retrieve execution details for a specific background job."""
    job = await job_service.get_job(db=db, tenant_id=current_user.organization_id, job_id=id)
    return StandardResponse(data=JobRead.model_validate(job))


@router.post("/{id}/retry", response_model=StandardResponse[JobRetryResponse], summary="Retry Failed/Dead-Letter Job")
async def retry_job(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[JobRetryResponse]:
    """Manually re-queues a failed or dead-letter background job."""
    job = await job_service.retry_job(db=db, tenant_id=current_user.organization_id, job_id=id)
    return StandardResponse(
        data=JobRetryResponse(job_id=job.id, status=job.status, message="Job reset to queued state for execution"),
        message="Background job re-queued successfully",
    )
