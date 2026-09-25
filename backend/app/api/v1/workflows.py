import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permission
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowExecutionRead,
    WorkflowRead,
    WorkflowUpdate,
)
from app.services import workflow_engine

router = APIRouter()


@router.get("", response_model=StandardResponse[List[WorkflowRead]], summary="List Workflows")
async def list_workflows_endpoint(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    trigger_event: Optional[str] = Query(None, description="Filter by trigger event"),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[WorkflowRead]]:
    workflows = await workflow_engine.list_workflows(
        db, current_user.organization_id, entity_type=entity_type, trigger_event=trigger_event
    )
    return StandardResponse(
        data=[WorkflowRead.model_validate(w) for w in workflows],
        message="Workflows retrieved successfully",
    )


@router.post("", response_model=StandardResponse[WorkflowRead], status_code=status.HTTP_201_CREATED, summary="Create Workflow")
async def create_workflow_endpoint(
    data: WorkflowCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[WorkflowRead]:
    wf = await workflow_engine.create_workflow(db, current_user.organization_id, data)
    return StandardResponse(data=WorkflowRead.model_validate(wf), message="Workflow created successfully")


@router.get("/executions", response_model=StandardResponse[List[WorkflowExecutionRead]], summary="List Workflow Executions")
async def list_executions_endpoint(
    workflow_id: Optional[uuid.UUID] = Query(None, description="Filter by workflow ID"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[WorkflowExecutionRead]]:
    executions = await workflow_engine.list_workflow_executions(
        db, current_user.organization_id, workflow_id=workflow_id, limit=limit
    )
    return StandardResponse(
        data=[WorkflowExecutionRead.model_validate(e) for e in executions],
        message="Workflow execution history retrieved",
    )


@router.get("/{workflow_id}", response_model=StandardResponse[WorkflowRead], summary="Get Workflow")
async def get_workflow_endpoint(
    workflow_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[WorkflowRead]:
    wf = await workflow_engine.get_workflow(db, current_user.organization_id, workflow_id)
    return StandardResponse(data=WorkflowRead.model_validate(wf), message="Workflow details")


@router.put("/{workflow_id}", response_model=StandardResponse[WorkflowRead], summary="Update Workflow")
async def update_workflow_endpoint(
    workflow_id: uuid.UUID,
    data: WorkflowUpdate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[WorkflowRead]:
    wf = await workflow_engine.update_workflow(db, current_user.organization_id, workflow_id, data)
    return StandardResponse(data=WorkflowRead.model_validate(wf), message="Workflow updated successfully")


@router.post("/{workflow_id}/activate", response_model=StandardResponse[WorkflowRead], summary="Activate Workflow")
async def activate_workflow_endpoint(
    workflow_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[WorkflowRead]:
    wf = await workflow_engine.update_workflow(
        db, current_user.organization_id, workflow_id, WorkflowUpdate(is_active=True)
    )
    return StandardResponse(data=WorkflowRead.model_validate(wf), message="Workflow activated")


@router.post("/{workflow_id}/deactivate", response_model=StandardResponse[WorkflowRead], summary="Deactivate Workflow")
async def deactivate_workflow_endpoint(
    workflow_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[WorkflowRead]:
    wf = await workflow_engine.update_workflow(
        db, current_user.organization_id, workflow_id, WorkflowUpdate(is_active=False)
    )
    return StandardResponse(data=WorkflowRead.model_validate(wf), message="Workflow deactivated")


@router.delete("/{workflow_id}", response_model=StandardResponse[Dict[str, Any]], summary="Delete Workflow")
async def delete_workflow_endpoint(
    workflow_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[Dict[str, Any]]:
    result = await workflow_engine.delete_workflow(db, current_user.organization_id, workflow_id)
    return StandardResponse(data=result, message=result["message"])


@router.post("/executions/{execution_id}/retry", response_model=StandardResponse[WorkflowExecutionRead], summary="Retry Failed Workflow Execution")
async def retry_execution_endpoint(
    execution_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[WorkflowExecutionRead]:
    exec_record = await workflow_engine.retry_workflow_execution(
        db, current_user.organization_id, execution_id
    )
    return StandardResponse(
        data=WorkflowExecutionRead.model_validate(exec_record),
        message="Workflow execution retried successfully",
    )
