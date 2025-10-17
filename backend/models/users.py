from pydantic import EmailStr
import uuid
from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .bookings import Booking


class UserInDB(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    email: EmailStr = Field(index=True, unique=True)
    password: str

    # Relationship to bookings
    bookings: List["Booking"] = Relationship(back_populates="user")
