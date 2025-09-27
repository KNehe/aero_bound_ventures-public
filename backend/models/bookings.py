from sqlmodel import SQLModel, Field, Relationship
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .users import UserInDB


class Booking(SQLModel, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False
    )
    user_id: uuid.UUID = Field(foreign_key="userindb.id", nullable=False)
    flight_order_id: str = Field(nullable=False)
    # Status could  be "pending", "confirmed", "cancelled"
    status: str = Field(default="pending", nullable=False)
    user: "UserInDB" = Relationship(back_populates="bookings")
