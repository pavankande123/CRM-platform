import datetime
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.custom_field import CustomField, CustomFieldValue
from app.schemas.custom_field import (
    CustomFieldCreate,
    CustomFieldUpdate,
    CustomFieldValueRead,
)


async def list_custom_fields(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    entity_type: Optional[str] = None,
    include_inactive: bool = False,
) -> List[CustomField]:
    stmt = select(CustomField).where(CustomField.tenant_id == tenant_id)
    if entity_type:
        stmt = stmt.where(CustomField.entity_type == entity_type.strip().lower())
    if not include_inactive:
        stmt = stmt.where(CustomField.is_active == True)  # noqa: E712
    stmt = stmt.order_by(CustomField.created_at.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_custom_field(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    field_id: uuid.UUID,
) -> CustomField:
    stmt = select(CustomField).where(
        CustomField.id == field_id,
        CustomField.tenant_id == tenant_id,
    )
    field = (await db.execute(stmt)).scalar_one_or_none()
    if not field:
        raise NotFoundError(message="Custom field definition not found.")
    return field


async def create_custom_field(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: CustomFieldCreate,
) -> CustomField:
    # Check compound uniqueness
    stmt = select(CustomField).where(
        CustomField.tenant_id == tenant_id,
        CustomField.entity_type == data.entity_type,
        CustomField.field_name == data.field_name,
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise ConflictError(message=f"Custom field '{data.field_name}' already exists for {data.entity_type}.")

    if data.field_type == "select" and not data.options:
        raise ValidationError(message="Options list is required for 'select' custom field type.")

    field = CustomField(
        tenant_id=tenant_id,
        entity_type=data.entity_type,
        field_name=data.field_name,
        display_name=data.display_name.strip(),
        field_type=data.field_type,
        is_required=data.is_required,
        is_searchable=data.is_searchable,
        is_active=data.is_active,
        options=data.options,
    )
    db.add(field)
    await db.commit()
    await db.refresh(field)
    return field


async def update_custom_field(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    field_id: uuid.UUID,
    data: CustomFieldUpdate,
) -> CustomField:
    field = await get_custom_field(db, tenant_id, field_id)
    if data.display_name is not None:
        field.display_name = data.display_name.strip()
    if data.is_required is not None:
        field.is_required = data.is_required
    if data.is_searchable is not None:
        field.is_searchable = data.is_searchable
    if data.is_active is not None:
        field.is_active = data.is_active
    if data.options is not None:
        if field.field_type == "select" and not data.options:
            raise ValidationError(message="Options cannot be empty for 'select' custom field type.")
        field.options = data.options

    await db.commit()
    await db.refresh(field)
    return field


async def delete_custom_field(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    field_id: uuid.UUID,
) -> dict:
    """Soft deactivates custom field to protect existing stored values."""
    field = await get_custom_field(db, tenant_id, field_id)
    field.is_active = False
    await db.commit()
    return {"status": "deactivated", "message": f"Custom field '{field.field_name}' deactivated successfully."}


async def get_entity_custom_field_values(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
) -> List[CustomFieldValueRead]:
    """Retrieve all custom field values for a specific record."""
    stmt = (
        select(CustomFieldValue)
        .options(selectinload(CustomFieldValue.field))
        .where(
            CustomFieldValue.tenant_id == tenant_id,
            CustomFieldValue.entity_type == entity_type.strip().lower(),
            CustomFieldValue.entity_id == entity_id,
        )
    )
    results = (await db.execute(stmt)).scalars().all()

    output: List[CustomFieldValueRead] = []
    for item in results:
        field = item.field
        if field:
            output.append(
                CustomFieldValueRead(
                    id=item.id,
                    tenant_id=item.tenant_id,
                    field_id=field.id,
                    field_name=field.field_name,
                    display_name=field.display_name,
                    field_type=field.field_type,
                    entity_type=item.entity_type,
                    entity_id=item.entity_id,
                    value=item.get_typed_value(),
                )
            )
    return output


async def set_entity_custom_field_values(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    values_dict: Dict[str, Any],
) -> List[CustomFieldValueRead]:
    """
    Sets or updates custom field values for a record.
    Validates types, required constraints, and select choices.
    """
    clean_entity_type = entity_type.strip().lower()
    fields = await list_custom_fields(db, tenant_id, entity_type=clean_entity_type, include_inactive=False)
    fields_by_key = {f.field_name: f for f in fields}
    fields_by_id = {str(f.id): f for f in fields}

    for key, raw_value in values_dict.items():
        field = fields_by_key.get(key) or fields_by_id.get(str(key))
        if not field:
            continue

        # Find existing value record
        stmt = select(CustomFieldValue).where(
            CustomFieldValue.tenant_id == tenant_id,
            CustomFieldValue.field_id == field.id,
            CustomFieldValue.entity_id == entity_id,
        )
        val_record = (await db.execute(stmt)).scalar_one_or_none()

        if raw_value is None or raw_value == "":
            if field.is_required:
                raise ValidationError(message=f"Field '{field.display_name}' is required.")
            if val_record:
                await db.delete(val_record)
            continue

        if not val_record:
            val_record = CustomFieldValue(
                tenant_id=tenant_id,
                field_id=field.id,
                entity_type=clean_entity_type,
                entity_id=entity_id,
            )
            db.add(val_record)

        # Reset columns
        val_record.value_text = None
        val_record.value_numeric = None
        val_record.value_date = None
        val_record.value_boolean = None

        ftype = field.field_type
        if ftype in ("number", "currency"):
            try:
                val_record.value_numeric = Decimal(str(raw_value))
            except Exception:
                raise ValidationError(message=f"Invalid numeric value '{raw_value}' for field '{field.display_name}'.")
        elif ftype == "date":
            try:
                if isinstance(raw_value, datetime.date):
                    val_record.value_date = raw_value
                else:
                    val_record.value_date = datetime.date.fromisoformat(str(raw_value).split("T")[0])
            except Exception:
                raise ValidationError(message=f"Invalid date format '{raw_value}' for field '{field.display_name}'. Expected YYYY-MM-DD.")
        elif ftype == "boolean":
            if isinstance(raw_value, bool):
                val_record.value_boolean = raw_value
            elif str(raw_value).lower() in ("true", "1", "yes"):
                val_record.value_boolean = True
            elif str(raw_value).lower() in ("false", "0", "no"):
                val_record.value_boolean = False
            else:
                raise ValidationError(message=f"Invalid boolean value '{raw_value}' for field '{field.display_name}'.")
        elif ftype == "select":
            str_val = str(raw_value).strip()
            if field.options and str_val not in field.options:
                raise ValidationError(message=f"Value '{str_val}' not in allowed options {field.options} for field '{field.display_name}'.")
            val_record.value_text = str_val
        else:
            # text
            val_record.value_text = str(raw_value)

    await db.commit()
    return await get_entity_custom_field_values(db, tenant_id, clean_entity_type, entity_id)
