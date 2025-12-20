from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, DateTime
import uuid
from typing import TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .users import UserInDB


class BookingStatus:
    CONFIRMED = "confirmed"
    PAID = "paid"
    CANCELLED = "cancelled"
    REVERSED = "reversed"
    FAILED = "failed"
    PENDING = "pending"
    REFUNDED = "refunded"


class Booking(SQLModel, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False
    )
    user_id: uuid.UUID = Field(foreign_key="userindb.id", nullable=False)
    flight_order_id: str = Field(nullable=False)

    status: str = Field(default=BookingStatus.CONFIRMED, nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    )
    total_price: float = Field(default=0.0, nullable=False)
    user: "UserInDB" = Relationship(back_populates="bookings")

    amadeus_order_response: dict | None = Field(default=None, sa_column=Column(JSON))
    ticket_url: str | None = Field(default=None, nullable=True)
