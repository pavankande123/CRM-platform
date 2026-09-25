import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permission
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.custom_field import (
    BulkCustomFieldValuesRequest,
    CustomFieldCreate,
    CustomFieldRead,
    CustomFieldUpdate,
    CustomFieldValueRead,
)
from app.services import custom_field_service

router = APIRouter()


@router.get("", response_model=StandardResponse[List[CustomFieldRead]], summary="List Custom Field Definitions")
async def list_custom_fields_endpoint(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (customer, project, product)"),
    include_inactive: bool = Query(False, description="Include deactivated fields"),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[CustomFieldRead]]:
    fields = await custom_field_service.list_custom_fields(
        db, current_user.organization_id, entity_type=entity_type, include_inactive=include_inactive
    )
    return StandardResponse(
        data=[CustomFieldRead.model_validate(f) for f in fields],
        message="Custom fields retrieved successfully",
    )


@router.post("", response_model=StandardResponse[CustomFieldRead], status_code=status.HTTP_201_CREATED, summary="Create Custom Field")
async def create_custom_field_endpoint(
    data: CustomFieldCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[CustomFieldRead]:
    field = await custom_field_service.create_custom_field(db, current_user.organization_id, data)
    return StandardResponse(data=CustomFieldRead.model_validate(field), message="Custom field created successfully")


@router.get("/{field_id}", response_model=StandardResponse[CustomFieldRead], summary="Get Custom Field")
async def get_custom_field_endpoint(
    field_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[CustomFieldRead]:
    field = await custom_field_service.get_custom_field(db, current_user.organization_id, field_id)
    return StandardResponse(data=CustomFieldRead.model_validate(field), message="Custom field details")


@router.put("/{field_id}", response_model=StandardResponse[CustomFieldRead], summary="Update Custom Field")
async def update_custom_field_endpoint(
    field_id: uuid.UUID,
    data: CustomFieldUpdate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[CustomFieldRead]:
    field = await custom_field_service.update_custom_field(db, current_user.organization_id, field_id, data)
    return StandardResponse(data=CustomFieldRead.model_validate(field), message="Custom field updated successfully")


@router.delete("/{field_id}", response_model=StandardResponse[Dict[str, Any]], summary="Deactivate Custom Field")
async def delete_custom_field_endpoint(
    field_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[Dict[str, Any]]:
    result = await custom_field_service.delete_custom_field(db, current_user.organization_id, field_id)
    return StandardResponse(data=result, message=result["message"])


@router.get("/values/{entity_type}/{entity_id}", response_model=StandardResponse[List[CustomFieldValueRead]], summary="Get Entity Custom Values")
async def get_entity_values_endpoint(
    entity_type: str,
    entity_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[CustomFieldValueRead]]:
    values = await custom_field_service.get_entity_custom_field_values(
        db, current_user.organization_id, entity_type, entity_id
    )
    return StandardResponse(data=values, message="Entity custom field values retrieved")


@router.post("/values/{entity_type}/{entity_id}", response_model=StandardResponse[List[CustomFieldValueRead]], summary="Set Entity Custom Values")
async def set_entity_values_endpoint(
    entity_type: str,
    entity_id: uuid.UUID,
    data: BulkCustomFieldValuesRequest,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[CustomFieldValueRead]]:
    values = await custom_field_service.set_entity_custom_field_values(
        db, current_user.organization_id, entity_type, entity_id, data.values
    )
    return StandardResponse(data=values, message="Entity custom field values saved successfully")
