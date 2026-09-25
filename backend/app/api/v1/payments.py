import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, StandardResponse
from app.schemas.payment import FinancialSummary, PaymentCreate, PaymentRead, PaymentUpdate
from app.services import payment_service

router = APIRouter()


@router.get("", response_model=StandardResponse[PaginatedResponse[PaymentRead]], summary="List Payments")
async def list_payments_endpoint(
    pagination: PaginationParams = Depends(),
    customer_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[PaginatedResponse[PaymentRead]]:
    items, total = await payment_service.list_payments(
        db=db,
        tenant_id=current_user.organization_id,
        customer_id=customer_id,
        project_id=project_id,
        status=status,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0
    return StandardResponse(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
        ),
        message="Payments retrieved successfully",
    )


@router.post("", response_model=StandardResponse[PaymentRead], status_code=status.HTTP_201_CREATED, summary="Record Payment")
async def create_payment_endpoint(
    data: PaymentCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[PaymentRead]:
    payment = await payment_service.create_payment(
        db=db,
        tenant_id=current_user.organization_id,
        data=data,
        actor_id=current_user.id,
    )
    return StandardResponse(
        data=PaymentRead.model_validate(payment),
        message="Payment recorded successfully",
    )


@router.get("/summary", response_model=StandardResponse[FinancialSummary], summary="Get Financial Balance Summary")
async def get_financial_summary_endpoint(
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[FinancialSummary]:
    summary = await payment_service.get_financial_summary(db, current_user.organization_id)
    return StandardResponse(data=summary, message="Financial summary computed")
