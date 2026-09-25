import uuid
from typing import Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.models.customer import Contact, Customer
from app.schemas.customer import ContactCreate, ContactUpdate, CustomerCreate, CustomerRead, CustomerUpdate
from app.services.activity_service import log_activity


async def list_customers(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    search: Optional[str] = None,
    status: Optional[str] = None,
    customer_type: Optional[str] = None,
    offset: int = 0,
    limit: int = 20,
) -> Tuple[list[CustomerRead], int]:
    """Retrieve paginated customers for tenant with contact metadata."""
    base_query = select(Customer).where(Customer.tenant_id == tenant_id)

    if status:
        base_query = base_query.where(Customer.status == status.lower())
    if customer_type:
        base_query = base_query.where(Customer.customer_type == customer_type.lower())
    if search:
        search_pattern = f"%{search.strip().lower()}%"
        base_query = base_query.where(
            or_(
                func.lower(Customer.name).like(search_pattern),
                func.lower(Customer.email).like(search_pattern),
                Customer.phone.like(f"%{search.strip()}%"),
                func.lower(Customer.city).like(search_pattern),
            )
        )

    # Count total
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Query with contacts eager-loaded
    stmt = (
        base_query
        .options(selectinload(Customer.contacts))
        .order_by(Customer.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    items = []
    for c in records:
        primary_contact = next((cnt for cnt in c.contacts if cnt.is_primary), None)
        if not primary_contact and c.contacts:
            primary_contact = c.contacts[0]

        items.append(
            CustomerRead(
                id=c.id,
                tenant_id=c.tenant_id,
                customer_type=c.customer_type,
                name=c.name,
                email=c.email,
                phone=c.phone,
                address_line1=c.address_line1,
                address_line2=c.address_line2,
                city=c.city,
                state=c.state,
                postal_code=c.postal_code,
                country=c.country,
                status=c.status,
                source=c.source,
                notes=c.notes,
                created_by_id=c.created_by_id,
                created_at=c.created_at,
                updated_at=c.updated_at,
                primary_contact_name=primary_contact.name if primary_contact else None,
                primary_contact_phone=primary_contact.phone if primary_contact else None,
            )
        )

    return items, total


async def create_customer(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: CustomerCreate,
    actor_id: Optional[uuid.UUID] = None,
) -> Customer:
    """Create customer and optional primary contact within tenant."""
    customer = Customer(
        tenant_id=tenant_id,
        customer_type=data.customer_type,
        name=data.name.strip(),
        email=data.email.lower().strip() if data.email else None,
        phone=data.phone.strip() if data.phone else None,
        address_line1=data.address_line1,
        address_line2=data.address_line2,
        city=data.city,
        state=data.state,
        postal_code=data.postal_code,
        country=data.country or "India",
        status=data.status or "active",
        source=data.source or "direct",
        notes=data.notes,
        created_by_id=actor_id,
    )
    db.add(customer)
    await db.flush()

    # Create primary contact if supplied
    if data.primary_contact:
        contact = Contact(
            tenant_id=tenant_id,
            customer_id=customer.id,
            name=data.primary_contact.name.strip(),
            designation=data.primary_contact.designation,
            phone=data.primary_contact.phone,
            email=data.primary_contact.email,
            is_primary=True,
            notes=data.primary_contact.notes,
        )
        db.add(contact)
        await db.flush()

    # Log business activity
    await log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type="CUSTOMER_CREATED",
        title=f"Customer created: {customer.name}",
        description=f"Type: {customer.customer_type} • Source: {customer.source}",
        customer_id=customer.id,
        actor_id=actor_id,
    )

    await db.commit()
    await db.refresh(customer)

    # Dispatch workflow event
    try:
        from app.services import workflow_engine
        await workflow_engine.dispatch_event(
            db=db,
            tenant_id=tenant_id,
            trigger_event="customer.created",
            entity_type="customer",
            entity_id=customer.id,
            record_data={
                "name": customer.name,
                "customer_type": customer.customer_type,
                "email": customer.email,
                "phone": customer.phone,
                "status": customer.status,
                "source": customer.source,
                "city": customer.city,
                "state": customer.state,
                "created_by_id": str(customer.created_by_id) if customer.created_by_id else None,
            },
        )
    except Exception as exc:
        logger.warning(f"Workflow dispatch error for customer.created: {exc}")

    return customer


async def get_customer(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
) -> Customer:
    """Fetch customer with all related 360 entities, strictly scoped to tenant."""
    stmt = (
        select(Customer)
        .options(
            selectinload(Customer.contacts),
            selectinload(Customer.projects),
            selectinload(Customer.payments),
            selectinload(Customer.follow_ups),
            selectinload(Customer.notes_rel),
            selectinload(Customer.documents),
            selectinload(Customer.activities),
        )
        .where(Customer.id == customer_id, Customer.tenant_id == tenant_id)
    )
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundError(message=f"Customer with ID {customer_id} not found.")
    return customer


async def update_customer(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    data: CustomerUpdate,
    actor_id: Optional[uuid.UUID] = None,
) -> Customer:
    """Update customer details."""
    customer = await get_customer(db, tenant_id, customer_id)

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(customer, field, val)

    await log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type="CUSTOMER_UPDATED",
        title=f"Customer updated: {customer.name}",
        customer_id=customer.id,
        actor_id=actor_id,
    )

    await db.commit()
    await db.refresh(customer)
    return customer


async def delete_customer(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
) -> None:
    """Delete a customer."""
    customer = await get_customer(db, tenant_id, customer_id)
    await db.delete(customer)
    await db.commit()


# --- Contact Operations ---

async def create_contact(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: uuid.UUID,
    data: ContactCreate,
) -> Contact:
    """Add a new contact person to a customer."""
    # Ensure customer exists in tenant
    await get_customer(db, tenant_id, customer_id)

    # If new contact is primary, unmark previous primaries
    if data.is_primary:
        stmt = select(Contact).where(Contact.customer_id == customer_id, Contact.tenant_id == tenant_id)
        existing = (await db.execute(stmt)).scalars().all()
        for c in existing:
            c.is_primary = False

    contact = Contact(
        tenant_id=tenant_id,
        customer_id=customer_id,
        name=data.name.strip(),
        designation=data.designation,
        phone=data.phone,
        email=data.email,
        is_primary=data.is_primary,
        notes=data.notes,
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
    data: ContactUpdate,
) -> Contact:
    """Update contact."""
    stmt = select(Contact).where(Contact.id == contact_id, Contact.tenant_id == tenant_id)
    contact = (await db.execute(stmt)).scalar_one_or_none()
    if not contact:
        raise NotFoundError(message="Contact not found.")

    update_dict = data.model_dump(exclude_unset=True)
    if update_dict.get("is_primary"):
        # Unmark existing primaries for this customer
        unmark_stmt = select(Contact).where(Contact.customer_id == contact.customer_id, Contact.tenant_id == tenant_id)
        existing = (await db.execute(unmark_stmt)).scalars().all()
        for c in existing:
            c.is_primary = False

    for field, val in update_dict.items():
        setattr(contact, field, val)

    await db.commit()
    await db.refresh(contact)
    return contact


async def delete_contact(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
) -> None:
    """Delete contact."""
    stmt = select(Contact).where(Contact.id == contact_id, Contact.tenant_id == tenant_id)
    contact = (await db.execute(stmt)).scalar_one_or_none()
    if not contact:
        raise NotFoundError(message="Contact not found.")
    await db.delete(contact)
    await db.commit()
