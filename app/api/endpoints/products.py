from decimal import Decimal
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import get_current_admin_user
from app.core.config import settings
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


class SortBy(str, Enum):
    name = "name"
    price = "price"
    stock = "stock_quantity"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


async_engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/", response_model=list[ProductResponse])
async def list_products(
    search: str | None = None,
    category: str | None = None,
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    in_stock: bool | None = None,
    sort_by: SortBy = SortBy.name,
    order: SortOrder = SortOrder.asc,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    query = select(Product).where(Product.is_active == True)

    if search:
        like = f"%{search}%"
        query = query.where(
            or_(Product.name.ilike(like), Product.description.ilike(like))
        )
    if category:
        query = query.where(Product.category == category)
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    if in_stock:
        query = query.where(Product.stock_quantity > 0)

    sort_column = getattr(Product, sort_by.value)
    query = query.order_by(
        asc(sort_column) if order == SortOrder.asc else desc(sort_column)
    )

    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return product


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(get_current_admin_user),
):
    product = Product(**product_in.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(get_current_admin_user),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(get_current_admin_user),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    await db.delete(product)
    await db.commit()
    return None
