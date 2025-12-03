from pydantic import EmailStr
import uuid
from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
from datetime import datetime

from .permissions import Group, Permission, UserGroup, UserPermission

if TYPE_CHECKING:
    from .bookings import Booking


class UserInDB(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    email: EmailStr = Field(index=True, unique=True)
    password: str
    reset_token: str | None = Field(default=None, nullable=True)
    reset_token_expires: datetime | None = Field(default=None, nullable=True)
    is_active: bool = Field(default=True, nullable=False)
    is_superuser: bool = Field(default=False, nullable=False)

    # Relationship to bookings
    bookings: list["Booking"] = Relationship(back_populates="user")

    # Relationships for RBAC
    groups: list["Group"] = Relationship(back_populates="users", link_model=UserGroup)
    permissions: list["Permission"] = Relationship(
        back_populates="users", link_model=UserPermission
    )
