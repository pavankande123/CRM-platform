import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permission
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.approval import (
    ApprovalDecisionCreate,
    ApprovalRequestCreate,
    ApprovalRequestRead,
)
from app.services import approval_service

router = APIRouter()


@router.get("", response_model=StandardResponse[List[ApprovalRequestRead]], summary="List Approval Requests")
async def list_approvals_endpoint(
    status: Optional[str] = Query(None, description="Filter by approval status (pending, approved, rejected)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (project, payment)"),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[ApprovalRequestRead]]:
    requests = await approval_service.list_approval_requests(
        db, current_user.organization_id, status=status, entity_type=entity_type
    )
    return StandardResponse(
        data=[ApprovalRequestRead.model_validate(r) for r in requests],
        message="Approval requests retrieved successfully",
    )


@router.post("", response_model=StandardResponse[ApprovalRequestRead], status_code=status.HTTP_201_CREATED, summary="Create Approval Request")
async def create_approval_endpoint(
    data: ApprovalRequestCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ApprovalRequestRead]:
    req = await approval_service.create_approval_request(
        db, current_user.organization_id, current_user.id, data
    )
    return StandardResponse(data=ApprovalRequestRead.model_validate(req), message="Approval request submitted")


@router.get("/{request_id}", response_model=StandardResponse[ApprovalRequestRead], summary="Get Approval Request")
async def get_approval_endpoint(
    request_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ApprovalRequestRead]:
    req = await approval_service.get_approval_request(db, current_user.organization_id, request_id)
    return StandardResponse(data=ApprovalRequestRead.model_validate(req), message="Approval request details")


@router.post("/{request_id}/decide", response_model=StandardResponse[ApprovalRequestRead], summary="Make Approval Decision")
async def decide_approval_endpoint(
    request_id: uuid.UUID,
    data: ApprovalDecisionCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ApprovalRequestRead]:
    req = await approval_service.decide_approval_request(
        db, current_user.organization_id, request_id, current_user, data
    )
    return StandardResponse(
        data=ApprovalRequestRead.model_validate(req),
        message=f"Approval request {data.decision} successfully",
    )
