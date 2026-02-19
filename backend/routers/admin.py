from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime, timedelta, timezone
from backend.crud.database import get_session
from backend.crud.bookings import (
    get_all_bookings_cursor,
)
from backend.utils.pagination import MAX_PAGINATION_LIMIT
from backend.models.bookings import Booking
from backend.models.constants import ADMIN_GROUP_NAME
from backend.schemas.admin import (
    BookingStatsResponse,
    AdminBookingResponse,
    CursorPaginatedAdminBookingResponse,
)
from backend.utils.dependencies import GroupDependency
from backend.utils.log_manager import get_app_logger

logger = get_app_logger(__name__)

router = APIRouter()


@router.get(
    "/stats/bookings",
    response_model=BookingStatsResponse,
    dependencies=[Depends(GroupDependency(ADMIN_GROUP_NAME))],
)
async def get_booking_stats(
    session: Session = Depends(get_session),
):
    """
    Get booking statistics for admin dashboard.

    Returns:
        - Total bookings count
        - Total revenue (sum of all booking amounts)
        - Active users count (users who have made bookings)
        - Bookings today count
        - Bookings this week count
    """
    logger.info("Calculating booking statistics")

    try:
        bookings = session.exec(select(Booking)).all()

        total_bookings = len(bookings)

        total_revenue = sum(booking.total_price for booking in bookings)

        # Calculate active users (unique users who have made bookings)
        unique_user_ids = set(booking.user_id for booking in bookings)
        active_users = len(unique_user_ids)

        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        bookings_today = sum(
            1 for booking in bookings if booking.created_at >= today_start
        )

        # Calculate bookings this week (last 7 days)
        one_week_ago = now - timedelta(days=7)
        bookings_this_week = sum(
            1 for booking in bookings if booking.created_at >= one_week_ago
        )

        stats = BookingStatsResponse(
            total_bookings=total_bookings,
            total_revenue=total_revenue,
            active_users=active_users,
            bookings_today=bookings_today,
            bookings_this_week=bookings_this_week,
        )

        logger.info(f"Successfully calculated booking statistics: {stats.model_dump()}")
        return stats

    except Exception:
        logger.exception("Error calculating booking statistics")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while calculating booking statistics",
        )


@router.get(
    "/bookings",
    response_model=CursorPaginatedAdminBookingResponse,
    dependencies=[Depends(GroupDependency(ADMIN_GROUP_NAME))],
)
async def get_all_bookings(
    cursor: str | None = Query(None, description="Cursor for pagination"),
    limit: int = Query(
        20,
        ge=1,
        le=MAX_PAGINATION_LIMIT,
        description="Maximum number of records to return",
    ),
    include_count: bool = Query(
        False,
        description="Include total_count in response (may be slower)",
    ),
    session: Session = Depends(get_session),
):
    """
    Get cursor-paginated bookings with user information for admin dashboard.

    Args:
        cursor: Cursor for pagination (None for first page)
        limit: Maximum number of records to return (default: 20, max: 100)

    Returns:
        Cursor-paginated list of bookings with associated user data
    """
    logger.info(
        f"Fetching bookings for admin dashboard with cursor={cursor}, limit={limit}"
    )

    try:
        bookings, next_cursor, has_more, total_count = get_all_bookings_cursor(
            session, cursor=cursor, limit=limit, include_count=include_count
        )

        items = []
        for booking in bookings:
            items.append(
                AdminBookingResponse(
                    id=booking.id,
                    flight_order_id=booking.flight_order_id,
                    status=booking.status,
                    created_at=booking.created_at,
                    ticket_url=booking.ticket_url,
                    total_price=booking.total_price,
                    user={
                        "id": booking.user.id,
                        "email": booking.user.email,
                    },
                    amadeus_order_response=booking.amadeus_order_response,
                )
            )

        response = CursorPaginatedAdminBookingResponse(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
            has_previous=cursor is not None,
            total_count=total_count,
            limit=limit,
        )

        logger.info(
            f"Successfully fetched {len(items)} bookings (has_more: {has_more})"
        )
        return response

    except Exception:
        logger.exception("Error fetching bookings for admin")
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching bookings"
        )


@router.get(
    "/bookings/{booking_id}",
    response_model=AdminBookingResponse,
    dependencies=[Depends(GroupDependency(ADMIN_GROUP_NAME))],
)
async def get_booking(
    booking_id: str,
    session: Session = Depends(get_session),
):
    """
    Get a single booking by ID for admin dashboard.

    Args:
        booking_id: The UUID of the booking to fetch

    Returns:
        Booking details with associated user data

    Raises:
        HTTPException 404: If booking not found
    """
    logger.info(f"Fetching booking {booking_id} for admin")

    try:
        statement = select(Booking).where(Booking.id == booking_id)
        booking = session.exec(statement).first()

        if not booking:
            logger.warning(f"Booking {booking_id} not found")
            raise HTTPException(status_code=404, detail="Booking not found")

        response = AdminBookingResponse(
            id=booking.id,
            flight_order_id=booking.flight_order_id,
            status=booking.status,
            created_at=booking.created_at,
            ticket_url=booking.ticket_url,
            total_price=booking.total_price,
            user={
                "id": booking.user.id,
                "email": booking.user.email,
            },
            amadeus_order_response=booking.amadeus_order_response,
        )

        logger.info(f"Successfully fetched booking {booking_id}")
        return response

    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Error fetching booking {booking_id}")
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching the booking"
        )
