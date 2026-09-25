import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permission
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.pipeline import (
    PipelineCreate,
    PipelineRead,
    PipelineUpdate,
    PipelineStageCreate,
    PipelineStageRead,
    PipelineStageUpdate,
    StageReorderRequest,
)
from app.services import pipeline_service

router = APIRouter()


@router.get("", response_model=StandardResponse[List[PipelineRead]], summary="List Pipelines")
async def list_pipelines_endpoint(
    include_inactive: bool = Query(False, description="Include deactivated pipelines"),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[PipelineRead]]:
    pipelines = await pipeline_service.list_pipelines(db, current_user.organization_id, include_inactive=include_inactive)
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


@router.put("/{pipeline_id}", response_model=StandardResponse[PipelineRead], summary="Update Pipeline")
async def update_pipeline_endpoint(
    pipeline_id: uuid.UUID,
    data: PipelineUpdate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[PipelineRead]:
    pipeline = await pipeline_service.update_pipeline(db, current_user.organization_id, pipeline_id, data)
    return StandardResponse(data=PipelineRead.model_validate(pipeline), message="Pipeline updated successfully")


@router.post("/{pipeline_id}/stages", response_model=StandardResponse[PipelineStageRead], status_code=status.HTTP_201_CREATED, summary="Create Pipeline Stage")
async def create_stage_endpoint(
    pipeline_id: uuid.UUID,
    data: PipelineStageCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[PipelineStageRead]:
    stage = await pipeline_service.create_stage(db, current_user.organization_id, pipeline_id, data)
    return StandardResponse(data=PipelineStageRead.model_validate(stage), message="Stage created successfully")


@router.put("/{pipeline_id}/stages/{stage_id}", response_model=StandardResponse[PipelineStageRead], summary="Update Pipeline Stage")
async def update_stage_endpoint(
    pipeline_id: uuid.UUID,
    stage_id: uuid.UUID,
    data: PipelineStageUpdate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[PipelineStageRead]:
    stage = await pipeline_service.update_stage(db, current_user.organization_id, pipeline_id, stage_id, data)
    return StandardResponse(data=PipelineStageRead.model_validate(stage), message="Stage updated successfully")


@router.post("/{pipeline_id}/stages/reorder", response_model=StandardResponse[List[PipelineStageRead]], summary="Reorder Pipeline Stages")
async def reorder_stages_endpoint(
    pipeline_id: uuid.UUID,
    data: StageReorderRequest,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[PipelineStageRead]]:
    stages = await pipeline_service.reorder_stages(db, current_user.organization_id, pipeline_id, data)
    return StandardResponse(
        data=[PipelineStageRead.model_validate(s) for s in stages],
        message="Stages reordered successfully",
    )


@router.delete("/{pipeline_id}/stages/{stage_id}", response_model=StandardResponse[Dict[str, Any]], summary="Safely Delete or Deactivate Stage")
async def delete_stage_endpoint(
    pipeline_id: uuid.UUID,
    stage_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[Dict[str, Any]]:
    result = await pipeline_service.deactivate_or_delete_stage(db, current_user.organization_id, pipeline_id, stage_id)
    return StandardResponse(data=result, message=result["message"])
