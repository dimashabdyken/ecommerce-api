from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_current_user, get_db
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse

router = APIRouter(prefix="/cart", tags=["cart"])


def _get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items))
        .filter(Cart.user_id == user_id)
        .first()
    )
    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.get("/", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = _get_or_create_cart(db, current_user.id)
    return cart


@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def add_cart_item(
    item_in: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if item_in.quantity < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be at least 1",
        )

    product = db.query(Product).filter(Product.id == item_in.product_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    cart = _get_or_create_cart(db, current_user.id)

    existing_item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == product.id)
        .first()
    )
    if existing_item is None:
        cart_item = CartItem(
            cart_id=cart.id, product_id=product.id, quantity=item_in.quantity
        )
        db.add(cart_item)
    else:
        existing_item.quantity += item_in.quantity

    db.commit()
    db.refresh(cart)
    return cart


@router.put("/items/{item_id}", response_model=CartResponse)
def update_cart_item(
    item_id: int,
    item_in: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if item_in.quantity < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be at least 1",
        )

    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items))
        .filter(Cart.user_id == current_user.id)
        .first()
    )
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    item.quantity = item_in.quantity
    db.commit()
    db.refresh(cart)
    return cart


@router.delete("/items/{item_id}", response_model=CartResponse)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items))
        .filter(Cart.user_id == current_user.id)
        .first()
    )
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    db.delete(item)
    db.commit()
    db.refresh(cart)
    return cart


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    db.delete(cart)
    db.commit()
    return None
