import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.pipeline import PipelineCreate, PipelineRead
from app.services import pipeline_service

router = APIRouter()


@router.get("", response_model=StandardResponse[List[PipelineRead]], summary="List Pipelines")
async def list_pipelines_endpoint(
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[PipelineRead]]:
    pipelines = await pipeline_service.list_pipelines(db, current_user.organization_id)
    return StandardResponse(
        data=[PipelineRead.model_validate(p) for p in pipelines],
        message="Pipelines retrieved successfully",
    )


@router.post("", response_model=StandardResponse[PipelineRead], status_code=status.HTTP_201_CREATED, summary="Create Pipeline")
async def create_pipeline_endpoint(
    data: PipelineCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[PipelineRead]:
    pipeline = await pipeline_service.create_pipeline(db, current_user.organization_id, data)
    return StandardResponse(data=PipelineRead.model_validate(pipeline), message="Pipeline created successfully")


@router.get("/{pipeline_id}", response_model=StandardResponse[PipelineRead], summary="Get Pipeline")
async def get_pipeline_endpoint(
    pipeline_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[PipelineRead]:
    pipeline = await pipeline_service.get_pipeline(db, current_user.organization_id, pipeline_id)
    return StandardResponse(data=PipelineRead.model_validate(pipeline), message="Pipeline details")
