from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.security import get_password_hash, verify_password
from app.models.address import Address
from app.models.user import User
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate
from app.schemas.user import (
    PasswordUpdate,
    UserProfileResponse,
    UserProfileUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


# user profile management


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile information."""
    return current_user


@router.put("/me", response_model=UserProfileResponse)
def update_user_profile(
    profile_update: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user's profile."""
    # Check if email is being changed and if it's already taken
    if profile_update.email and profile_update.email != current_user.email:
        existing_user = (
            db.query(User).filter(User.email == profile_update.email).first()
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        current_user.email = profile_update.email

    # Update phone number if provided
    if profile_update.phone_number is not None:
        current_user.phone_number = profile_update.phone_number

    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me/password")
def change_password(
    password_update: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change user's password."""
    # Verify current password
    if not verify_password(
        password_update.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update to new password
    current_user.hashed_password = get_password_hash(password_update.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


# address management


@router.get("/me/addresses", response_model=list[AddressResponse])
def get_user_addresses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all addresses for the current user."""
    addresses = (
        db.query(Address)
        .filter(Address.user_id == current_user.id)
        .order_by(Address.is_default.desc(), Address.created_at.desc())
        .all()
    )
    return addresses


@router.post(
    "/me/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED
)
def create_address(
    address: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new address for the current user."""
    if address.is_default:
        db.query(Address).filter(
            Address.user_id == current_user.id, Address.is_default.is_(True)
        ).update({"is_default": False})

    # Create new address
    new_address = Address(**address.model_dump(), user_id=current_user.id)
    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    return new_address


@router.get("/me/addresses/{address_id}", response_model=AddressResponse)
def get_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific address."""
    address = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == current_user.id)
        .first()
    )

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Address not found"
        )

    return address


@router.put("/me/addresses/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: int,
    address_update: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing address."""
    address = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == current_user.id)
        .first()
    )

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Address not found"
        )

    if address_update.is_default and not address.is_default:
        db.query(Address).filter(
            Address.user_id == current_user.id,
            Address.id != address_id,
            Address.is_default.is_(True),
        ).update({"is_default": False})

    # Update address fields
    update_data = address_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)

    return address


# delete user address and set default address


@router.delete("/me/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an address."""
    address = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == current_user.id)
        .first()
    )

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Address not found"
        )

    db.delete(address)
    db.commit()

    return None


@router.put("/me/addresses/{address_id}/default", response_model=AddressResponse)
def set_default_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set an address as the default."""
    address = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == current_user.id)
        .first()
    )

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Address not found"
        )

    # Unset all other defaults for this user
    db.query(Address).filter(
        Address.user_id == current_user.id, Address.id != address_id
    ).update({"is_default": False})

    # Set this one as default
    address.is_default = True
    db.commit()
    db.refresh(address)

    return address
