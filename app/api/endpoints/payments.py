import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.config import settings
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.order import CheckoutRequest, CheckoutResponse, OrderResponse
from app.services.email import send_order_confirmation_email

router = APIRouter(prefix="/payments", tags=["payments"])

stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout_session(
    checkout_request: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a Stripe PaymentIntent from the user's cart."""
    # Get user's cart
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()

    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty"
        )

    # Validate stock availability before creating order
    for cart_item in cart.items:
        if cart_item.product.stock_quantity < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{cart_item.product.name}': "
                f"requested {cart_item.quantity}, available {cart_item.product.stock_quantity}",
            )

    # Calculate total amount
    total_amount = sum(item.quantity * item.product.price for item in cart.items)

    # Create order in pending status
    order = Order(
        user_id=current_user.id, total_amount=total_amount, status=OrderStatus.PENDING
    )
    db.add(order)
    db.flush()  # Get order.id

    # Create order items
    for cart_item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price_at_purchase=cart_item.product.price,
        )
        db.add(order_item)

    # Create Stripe PaymentIntent
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(total_amount * 100),  # Convert to cents
            currency="usd",
            metadata={"order_id": order.id, "user_id": current_user.id},
        )

        order.stripe_payment_intent_id = payment_intent.id
        db.commit()

        return CheckoutResponse(
            client_secret=payment_intent.client_secret, order_id=order.id
        )

    except stripe.error.StripeError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stripe error: {str(e)}"
        )


@router.get("/orders", response_model=list[OrderResponse])
def get_user_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all orders for the current user."""
    orders = db.query(Order).filter(Order.user_id == current_user.id).all()
    return orders


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific order by ID."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return order


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    # Handle the event
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        order_id = payment_intent["metadata"].get("order_id")

        if order_id:
            order = db.query(Order).filter(Order.id == int(order_id)).first()
            if order:
                order.status = OrderStatus.PAID

                # Decrement stock for each purchased item
                for item in order.items:
                    product = (
                        db.query(Product).filter(Product.id == item.product_id).first()
                    )
                    if product:
                        product.stock_quantity = max(
                            0, product.stock_quantity - item.quantity
                        )

                # Clear user's cart after successful payment
                cart = db.query(Cart).filter(Cart.user_id == order.user_id).first()
                if cart:
                    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

                db.commit()

                # Refresh order to load relationships for email
                db.refresh(order)

                # Send order confirmation email
                await send_order_confirmation_email(
                    to_email=order.user.email, order=order
                )

    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        order_id = payment_intent["metadata"].get("order_id")

        if order_id:
            order = db.query(Order).filter(Order.id == int(order_id)).first()
            if order:
                order.status = OrderStatus.CANCELED
                db.commit()

    return {"status": "success"}


@router.post("/orders/{order_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending order (before payment)."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status '{order.status}'. Only PENDING orders can be cancelled.",
        )

    order.status = OrderStatus.CANCELED
    db.commit()

    return {
        "message": f"Order #{order_id} cancelled successfully",
        "order_id": order_id,
    }


@router.post("/orders/{order_id}/refund", status_code=status.HTTP_200_OK)
def refund_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Refund a paid order and restore stock."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    if order.status != OrderStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot refund order with status '{order.status}'. Only PAID orders can be refunded.",
        )

    if not order.stripe_payment_intent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No payment intent found for this order",
        )

    # Process Stripe refund
    try:
        refund = stripe.Refund.create(payment_intent=order.stripe_payment_intent_id)

        if refund.status == "succeeded":
            # Update order status
            order.status = OrderStatus.REFUNDED

            # Restore stock for each item
            for item in order.items:
                product = (
                    db.query(Product).filter(Product.id == item.product_id).first()
                )
                if product:
                    product.stock_quantity += item.quantity

            db.commit()

            return {
                "message": f"Order #{order_id} refunded successfully",
                "order_id": order_id,
                "refund_id": refund.id,
                "amount_refunded": refund.amount / 100,  # Convert cents to dollars
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Refund failed with status: {refund.status}",
            )

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe refund error: {str(e)}",
        )
