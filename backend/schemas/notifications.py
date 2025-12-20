from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Optional, Any


class NotificationBase(BaseModel):
    message: str
    type: str


class NotificationCreate(NotificationBase):
    user_id: uuid.UUID


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationStreamEvent(BaseModel):
    event_type: str  # "notification", "unread_count", "connected"
    data: dict[str, Any]


class UnreadCountResponse(BaseModel):
    unread_count: int