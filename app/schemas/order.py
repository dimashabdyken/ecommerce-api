from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_at_purchase: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: Decimal
    status: str
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


class CheckoutRequest(BaseModel):
    """Request to create a checkout session from cart."""

    pass


class CheckoutResponse(BaseModel):
    """Response with Stripe client secret for payment."""

    client_secret: str
    order_id: int
