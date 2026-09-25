import uuid
from typing import Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate


async def list_products(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    offset: int = 0,
    limit: int = 50,
) -> Tuple[list[Product], int]:
    base_query = select(Product).where(Product.tenant_id == tenant_id)

    if category:
        base_query = base_query.where(Product.category == category)
    if is_active is not None:
        base_query = base_query.where(Product.is_active == is_active)

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base_query.order_by(Product.name.asc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().all()
    return list(products), total


async def create_product(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: ProductCreate,
) -> Product:
    product = Product(
        tenant_id=tenant_id,
        name=data.name.strip(),
        code=data.code.strip() if data.code else None,
        category=data.category.strip() if data.category else None,
        description=data.description,
        unit_price=data.unit_price,
        is_active=data.is_active,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def get_product(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
) -> Product:
    stmt = select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id)
    product = (await db.execute(stmt)).scalar_one_or_none()
    if not product:
        raise NotFoundError(message=f"Product with ID {product_id} not found.")
    return product


async def update_product(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    data: ProductUpdate,
) -> Product:
    product = await get_product(db, tenant_id, product_id)
    update_dict = data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(product, k, v)
    await db.commit()
    await db.refresh(product)
    return product
