from pydantic import BaseModel, Field
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


class PaginatedUserBookingResponse(BaseModel):
    """Paginated response model for user's booking list"""

    items: list[UserBookingResponse]
    total: int = Field(description="Total number of bookings")
    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Maximum number of items returned")


class BookingCancellationResponse(BaseModel):
    """Response model for booking cancellation"""

    id: uuid.UUID
    status: str
    message: str
