from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    street_address: Mapped[str] = mapped_column(String(500))
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    zip_code: Mapped[str] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(100))
    phone_number: Mapped[str] = mapped_column(String(20))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Relationships
    user: Mapped[User] = relationship(back_populates="addresses")
