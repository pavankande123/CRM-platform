import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, StandardResponse
from app.schemas.project import ProjectCreate, ProjectDetailRead, ProjectRead, ProjectStageChange, ProjectUpdate
from app.services import project_service

router = APIRouter()


@router.get("", response_model=StandardResponse[PaginatedResponse[ProjectRead]], summary="List Projects")
async def list_projects_endpoint(
    pagination: PaginationParams = Depends(),
    customer_id: Optional[uuid.UUID] = Query(None),
    stage_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[PaginatedResponse[ProjectRead]]:
    items, total = await project_service.list_projects(
        db=db,
        tenant_id=current_user.organization_id,
        customer_id=customer_id,
        stage_id=stage_id,
        status=status,
        search=search,
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
        message="Projects retrieved successfully",
    )


@router.post("", response_model=StandardResponse[ProjectRead], status_code=status.HTTP_201_CREATED, summary="Create Project")
async def create_project_endpoint(
    data: ProjectCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ProjectRead]:
    project = await project_service.create_project(
        db=db,
        tenant_id=current_user.organization_id,
        data=data,
        actor_id=current_user.id,
    )
    full_project = await project_service.get_project(db, current_user.organization_id, project.id)
    return StandardResponse(
        data=ProjectRead(
            id=full_project.id,
            tenant_id=full_project.tenant_id,
            project_number=full_project.project_number,
            name=full_project.name,
            customer_id=full_project.customer_id,
            product_id=full_project.product_id,
            pipeline_id=full_project.pipeline_id,
            stage_id=full_project.stage_id,
            description=full_project.description,
            value=full_project.value,
            currency=full_project.currency,
            expected_completion_date=full_project.expected_completion_date,
            status=full_project.status,
            priority=full_project.priority,
            owner_id=full_project.owner_id,
            customer_name=full_project.customer.name if full_project.customer else None,
            product_name=full_project.product.name if full_project.product else None,
            pipeline_name=full_project.pipeline.name if full_project.pipeline else None,
            stage_name=full_project.stage.name if full_project.stage else None,
            stage_color=full_project.stage.color if full_project.stage else None,
            owner_name=full_project.owner.full_name if full_project.owner else None,
            created_at=full_project.created_at,
            updated_at=full_project.updated_at,
        ),
        message="Project created successfully",
    )


@router.get("/{project_id}", response_model=StandardResponse[ProjectDetailRead], summary="Get Project Detail")
async def get_project_endpoint(
    project_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ProjectDetailRead]:
    p = await project_service.get_project(db, current_user.organization_id, project_id)
    from decimal import Decimal
    total_paid = sum((pm.amount for pm in p.payments if pm.status == "received"), Decimal("0.00"))
    outstanding = max(Decimal("0.00"), p.value - total_paid)

    history = [
        {
            "id": h.id,
            "project_id": h.project_id,
            "from_stage_id": h.from_stage_id,
            "from_stage_name": h.from_stage.name if h.from_stage else None,
            "to_stage_id": h.to_stage_id,
            "to_stage_name": h.to_stage.name if h.to_stage else "Stage",
            "changed_by_id": h.changed_by_id,
            "changed_by_name": h.changed_by.full_name if h.changed_by else None,
            "notes": h.notes,
            "changed_at": h.changed_at,
        }
        for h in p.stage_history
    ]
    history.sort(
        key=lambda h: (h["changed_at"] or datetime.datetime.min, h["from_stage_id"] is not None),
        reverse=True,
    )

    return StandardResponse(
        data=ProjectDetailRead(
            id=p.id,
            tenant_id=p.tenant_id,
            project_number=p.project_number,
            name=p.name,
            customer_id=p.customer_id,
            product_id=p.product_id,
            pipeline_id=p.pipeline_id,
            stage_id=p.stage_id,
            description=p.description,
            value=p.value,
            currency=p.currency,
            expected_completion_date=p.expected_completion_date,
            status=p.status,
            priority=p.priority,
            owner_id=p.owner_id,
            customer_name=p.customer.name if p.customer else None,
            product_name=p.product.name if p.product else None,
            pipeline_name=p.pipeline.name if p.pipeline else None,
            stage_name=p.stage.name if p.stage else None,
            stage_color=p.stage.color if p.stage else None,
            owner_name=p.owner.full_name if p.owner else None,
            total_paid=total_paid,
            outstanding_amount=outstanding,
            stage_history=history,
            created_at=p.created_at,
            updated_at=p.updated_at,
        ),
        message="Project details retrieved",
    )


@router.post("/{project_id}/stage", response_model=StandardResponse[dict], summary="Transition Project Stage")
async def change_stage_endpoint(
    project_id: uuid.UUID,
    data: ProjectStageChange,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[dict]:
    project = await project_service.change_project_stage(
        db=db,
        tenant_id=current_user.organization_id,
        project_id=project_id,
        data=data,
        actor_id=current_user.id,
    )
    return StandardResponse(
        data={"project_id": str(project.id), "new_stage_id": str(project.stage_id), "status": project.status},
        message="Project transitioned to new stage successfully",
    )


@router.patch("/{project_id}", response_model=StandardResponse[ProjectRead], summary="Update Project")
async def update_project_endpoint(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ProjectRead]:
    project = await project_service.update_project(
        db=db,
        tenant_id=current_user.organization_id,
        project_id=project_id,
        data=data,
        actor_id=current_user.id,
    )
    full_project = await project_service.get_project(db, current_user.organization_id, project.id)
    return StandardResponse(
        data=ProjectRead(
            id=full_project.id,
            tenant_id=full_project.tenant_id,
            project_number=full_project.project_number,
            name=full_project.name,
            customer_id=full_project.customer_id,
            product_id=full_project.product_id,
            pipeline_id=full_project.pipeline_id,
            stage_id=full_project.stage_id,
            description=full_project.description,
            value=full_project.value,
            currency=full_project.currency,
            expected_completion_date=full_project.expected_completion_date,
            status=full_project.status,
            priority=full_project.priority,
            owner_id=full_project.owner_id,
            customer_name=full_project.customer.name if full_project.customer else None,
            product_name=full_project.product.name if full_project.product else None,
            pipeline_name=full_project.pipeline.name if full_project.pipeline else None,
            stage_name=full_project.stage.name if full_project.stage else None,
            stage_color=full_project.stage.color if full_project.stage else None,
            owner_name=full_project.owner.full_name if full_project.owner else None,
            created_at=full_project.created_at,
            updated_at=full_project.updated_at,
        ),
        message="Project updated successfully",
    )
