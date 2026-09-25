import uuid
from decimal import Decimal
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.product import Product
from app.models.project import Project
from app.schemas.customer import CustomerRead
from app.schemas.product import ProductRead
from app.schemas.project import ProjectRead
from app.schemas.search import SearchResponse


async def global_search(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    query: str,
    limit_per_category: int = 10,
) -> SearchResponse:
    """
    Search across customers, projects, and products using PostgreSQL text filtering.
    Cleanly encapsulated so full-text/search engine can be plugged in later if required.
    Strictly tenant-scoped.
    """
    clean_q = query.strip()
    if not clean_q:
        return SearchResponse(query=query, customers=[], projects=[], products=[], total_results=0)

    pattern = f"%{clean_q.lower()}%"

    # 1. Search Customers
    cust_stmt = (
        select(Customer)
        .options(selectinload(Customer.contacts))
        .where(
            Customer.tenant_id == tenant_id,
            or_(
                func.lower(Customer.name).like(pattern),
                func.lower(Customer.email).like(pattern),
                Customer.phone.like(f"%{clean_q}%"),
                func.lower(Customer.city).like(pattern),
            ),
        )
        .order_by(Customer.created_at.desc())
        .limit(limit_per_category)
    )
    cust_results = (await db.execute(cust_stmt)).scalars().all()
    customers_out = [
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
            primary_contact_name=c.contacts[0].name if c.contacts else None,
            primary_contact_phone=c.contacts[0].phone if c.contacts else None,
        )
        for c in cust_results
    ]

    # 2. Search Projects
    proj_stmt = (
        select(Project)
        .options(
            selectinload(Project.customer),
            selectinload(Project.product),
            selectinload(Project.pipeline),
            selectinload(Project.stage),
            selectinload(Project.owner),
            selectinload(Project.payments),
        )
        .where(
            Project.tenant_id == tenant_id,
            or_(
                func.lower(Project.name).like(pattern),
                func.lower(Project.project_number).like(pattern),
            ),
        )
        .order_by(Project.created_at.desc())
        .limit(limit_per_category)
    )
    proj_results = (await db.execute(proj_stmt)).scalars().all()
    projects_out = []
    for p in proj_results:
        total_paid = sum((pm.amount for pm in p.payments if pm.status == "received"), Decimal("0.00"))
        outstanding = max(Decimal("0.00"), p.value - total_paid)
        projects_out.append(
            ProjectRead(
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
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    # 3. Search Products
    prod_stmt = (
        select(Product)
        .where(
            Product.tenant_id == tenant_id,
            or_(
                func.lower(Product.name).like(pattern),
                func.lower(Product.code).like(pattern),
            ),
        )
        .order_by(Product.name.asc())
        .limit(limit_per_category)
    )
    prod_results = (await db.execute(prod_stmt)).scalars().all()
    products_out = [ProductRead.model_validate(pr) for pr in prod_results]

    total_count = len(customers_out) + len(projects_out) + len(products_out)

    return SearchResponse(
        query=query,
        customers=customers_out,
        projects=projects_out,
        products=products_out,
        total_results=total_count,
    )
