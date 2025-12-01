from pydantic import BaseModel
import uuid
from datetime import datetime


class BookingResponse(BaseModel):
    id: uuid.UUID
    flight_order_id: str
    status: str


class UserBookingResponse(BaseModel):
    """Response model for user's booking list"""
    id: uuid.UUID
    pnr: str | None
    status: str
    created_at: datetime
    ticket_url: str | None
