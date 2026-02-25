from decimal import Decimal

from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: Decimal
    stock_quantity: int
    category: str
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    stock_quantity: int | None = None
    category: str | None = None
    is_active: bool | None = None


class ProductResponse(ProductBase):
    id: int

    class Config:
        orm_mode = True
