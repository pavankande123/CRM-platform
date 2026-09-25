import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, StandardResponse
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import product_service

router = APIRouter()


@router.get("", response_model=StandardResponse[PaginatedResponse[ProductRead]], summary="List Products")
async def list_products_endpoint(
    pagination: PaginationParams = Depends(),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[PaginatedResponse[ProductRead]]:
    items, total = await product_service.list_products(
        db, current_user.organization_id, category, is_active, pagination.offset, pagination.page_size
    )
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0
    return StandardResponse(
        data=PaginatedResponse(
            items=[ProductRead.model_validate(p) for p in items],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
        ),
        message="Products retrieved successfully",
    )


@router.post("", response_model=StandardResponse[ProductRead], status_code=status.HTTP_201_CREATED, summary="Create Product")
async def create_product_endpoint(
    data: ProductCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ProductRead]:
    product = await product_service.create_product(db, current_user.organization_id, data)
    return StandardResponse(data=ProductRead.model_validate(product), message="Product created successfully")


@router.get("/{product_id}", response_model=StandardResponse[ProductRead], summary="Get Product")
async def get_product_endpoint(
    product_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ProductRead]:
    product = await product_service.get_product(db, current_user.organization_id, product_id)
    return StandardResponse(data=ProductRead.model_validate(product), message="Product details")


@router.patch("/{product_id}", response_model=StandardResponse[ProductRead], summary="Update Product")
async def update_product_endpoint(
    product_id: uuid.UUID,
    data: ProductUpdate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[ProductRead]:
    product = await product_service.update_product(db, current_user.organization_id, product_id, data)
    return StandardResponse(data=ProductRead.model_validate(product), message="Product updated successfully")
