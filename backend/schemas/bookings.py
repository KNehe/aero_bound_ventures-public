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


class CursorPaginatedUserBookingResponse(BaseModel):
    """Cursor-based paginated response model for user's booking list"""

    items: list[UserBookingResponse]
    next_cursor: str | None = Field(
        description="Cursor for the next page, null if no more pages"
    )
    has_more: bool = Field(description="Whether there are more items after this page")
    has_previous: bool = Field(
        default=False, description="Whether there are items before this page"
    )
    total_count: int | None = Field(
        default=None, description="Total count (null if not requested)"
    )
    limit: int = Field(description="Maximum number of items returned")


class BookingCancellationResponse(BaseModel):
    """Response model for booking cancellation"""

    id: uuid.UUID
    status: str
    message: str
