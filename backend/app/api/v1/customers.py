import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, StandardResponse
from app.schemas.customer import (
    ContactCreate,
    ContactRead,
    ContactUpdate,
    CustomerCreate,
    CustomerDetailRead,
    CustomerRead,
    CustomerUpdate,
)
from app.services import customer_service

router = APIRouter()


@router.get("", response_model=StandardResponse[PaginatedResponse[CustomerRead]], summary="List Customers")
async def list_customers_endpoint(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search by name, email, phone, city"),
    status: Optional[str] = Query(None, description="Filter by status (active, lead, inactive)"),
    customer_type: Optional[str] = Query(None, description="Filter by type (commercial, industrial, etc.)"),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[PaginatedResponse[CustomerRead]]:
    items, total = await customer_service.list_customers(
        db=db,
        tenant_id=current_user.organization_id,
        search=search,
        status=status,
        customer_type=customer_type,
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
        message="Customers retrieved successfully",
    )


@router.post("", response_model=StandardResponse[CustomerRead], status_code=status.HTTP_201_CREATED, summary="Create Customer")
async def create_customer_endpoint(
    data: CustomerCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[CustomerRead]:
    customer = await customer_service.create_customer(
        db=db,
        tenant_id=current_user.organization_id,
        data=data,
        actor_id=current_user.id,
    )
    read_data = CustomerRead.model_validate(customer)
    if customer.contacts:
        read_data.primary_contact_name = customer.contacts[0].name
        read_data.primary_contact_phone = customer.contacts[0].phone

    return StandardResponse(
        data=read_data,
        message="Customer created successfully",
    )


@router.get("/{customer_id}", response_model=StandardResponse[CustomerDetailRead], summary="Get Customer Detail")
async def get_customer_endpoint(
    customer_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[CustomerDetailRead]:
    customer = await customer_service.get_customer(db, current_user.organization_id, customer_id)
    return StandardResponse(
        data=CustomerDetailRead.model_validate(customer),
        message="Customer details retrieved",
    )


@router.patch("/{customer_id}", response_model=StandardResponse[CustomerRead], summary="Update Customer")
async def update_customer_endpoint(
    customer_id: uuid.UUID,
    data: CustomerUpdate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[CustomerRead]:
    customer = await customer_service.update_customer(
        db=db,
        tenant_id=current_user.organization_id,
        customer_id=customer_id,
        data=data,
        actor_id=current_user.id,
    )
    return StandardResponse(
        data=CustomerRead.model_validate(customer),
        message="Customer updated successfully",
    )


@router.delete("/{customer_id}", response_model=StandardResponse[dict], summary="Delete Customer")
async def delete_customer_endpoint(
    customer_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:delete")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[dict]:
    await customer_service.delete_customer(db, current_user.organization_id, customer_id)
    return StandardResponse(data={"deleted": True}, message="Customer deleted successfully")


# --- Contact Sub-resource Endpoints ---

@router.post("/{customer_id}/contacts", response_model=StandardResponse[ContactRead], status_code=status.HTTP_201_CREATED, summary="Add Customer Contact")
async def create_contact_endpoint(
    customer_id: uuid.UUID,
    data: ContactCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ContactRead]:
    contact = await customer_service.create_contact(db, current_user.organization_id, customer_id, data)
    return StandardResponse(data=ContactRead.model_validate(contact), message="Contact added successfully")


@router.patch("/contacts/{contact_id}", response_model=StandardResponse[ContactRead], summary="Update Contact")
async def update_contact_endpoint(
    contact_id: uuid.UUID,
    data: ContactUpdate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ContactRead]:
    contact = await customer_service.update_contact(db, current_user.organization_id, contact_id, data)
    return StandardResponse(data=ContactRead.model_validate(contact), message="Contact updated successfully")


@router.delete("/contacts/{contact_id}", response_model=StandardResponse[dict], summary="Delete Contact")
async def delete_contact_endpoint(
    contact_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:delete")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[dict]:
    await customer_service.delete_contact(db, current_user.organization_id, contact_id)
    return StandardResponse(data={"deleted": True}, message="Contact deleted successfully")
