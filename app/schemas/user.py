from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    """Extended user profile with phone number."""

    id: int
    email: str
    phone_number: str | None = None
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""

    email: EmailStr | None = None
    phone_number: str | None = Field(None, min_length=1, max_length=20)


class PasswordUpdate(BaseModel):
    """Schema for changing password."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
