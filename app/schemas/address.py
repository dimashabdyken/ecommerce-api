from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class AddressBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    street_address: str = Field(..., min_length=1, max_length=500)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    zip_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(..., min_length=1, max_length=20)
    is_default: bool = False

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Basic phone validation - remove spaces and check format."""
        cleaned = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not cleaned.startswith("+"):
            raise ValueError("Phone number must start with country code (e.g., +1)")
        if len(cleaned) < 10:
            raise ValueError("Phone number too short")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str) -> str:
        """Ensure zip code is alphanumeric."""
        if not v.replace(" ", "").replace("-", "").isalnum():
            raise ValueError("Invalid zip code format")
        return v


class AddressCreate(AddressBase):
    """Schema for creating a new address."""

    pass


class AddressUpdate(BaseModel):
    """Schema for updating an address - all fields optional."""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    street_address: str | None = Field(None, min_length=1, max_length=500)
    city: str | None = Field(None, min_length=1, max_length=100)
    state: str | None = Field(None, min_length=1, max_length=100)
    zip_code: str | None = Field(None, min_length=1, max_length=20)
    country: str | None = Field(None, min_length=2, max_length=100)
    phone_number: str | None = Field(None, min_length=1, max_length=20)
    is_default: bool | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Basic phone validation."""
        if v is None:
            return v
        cleaned = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not cleaned.startswith("+"):
            raise ValueError("Phone number must start with country code (e.g., +1)")
        if len(cleaned) < 10:
            raise ValueError("Phone number too short")
        return v


class AddressResponse(AddressBase):
    """Schema for address in responses."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
