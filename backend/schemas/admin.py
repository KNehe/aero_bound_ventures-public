from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class AdminUserInfo(BaseModel):
    """User information in admin booking response"""

    id: uuid.UUID
    email: str


class AdminBookingResponse(BaseModel):
    """Response model for individual booking in admin dashboard"""

    id: uuid.UUID
    flight_order_id: str
    status: str
    created_at: datetime
    ticket_url: str | None
    total_price: float
    user: AdminUserInfo
    amadeus_order_response: dict | None

    class Config:
        from_attributes = True


class CursorPaginatedAdminBookingResponse(BaseModel):
    """Cursor-based paginated response model for admin booking list"""

    items: list[AdminBookingResponse]
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


class BookingStatsResponse(BaseModel):
    """Response model for booking statistics on admin dashboard"""

    total_bookings: int = Field(description="Total number of bookings in the system")
    total_revenue: float = Field(description="Total revenue from all bookings")
    active_users: int = Field(
        description="Number of unique users who have made bookings"
    )
    bookings_today: int = Field(description="Number of bookings created today")
    bookings_this_week: int = Field(
        description="Number of bookings created in the last 7 days"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_bookings": 150,
                "total_revenue": 45678.90,
                "active_users": 87,
                "bookings_today": 5,
                "bookings_this_week": 23,
            }
        }
