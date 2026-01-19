from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, Index
from typing import TYPE_CHECKING
import uuid
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .users import UserInDB


class NotificationType:
    TICKET_UPLOADED = "ticket_uploaded"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    PASSWORD_CHANGED = "password_changed"
    GENERAL = "general"


class Notification(SQLModel, table=True):
    """Notification model - represents notifications sent to users"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    user_id: uuid.UUID = Field(foreign_key="userindb.id", nullable=False)
    type: str = Field(default=NotificationType.GENERAL, nullable=False)
    message: str = Field(nullable=False)
    is_read: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            default=lambda: datetime.now(timezone.utc),
        )
    )
    user: "UserInDB" = Relationship(back_populates="notifications")

    __table_args__ = (
        Index("ix_notification_user_cursor", "user_id", "created_at", "id"),
    )
