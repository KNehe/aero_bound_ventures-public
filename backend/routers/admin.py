from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime, timedelta, timezone
from backend.crud.database import get_session
from backend.crud.bookings import (
    get_all_bookings_paginated,
    get_all_bookings_count,
    MAX_PAGINATION_LIMIT,
)
from backend.models.bookings import Booking
from backend.models.constants import ADMIN_GROUP_NAME
from backend.schemas.admin import (
    BookingStatsResponse,
    AdminBookingResponse,
    PaginatedAdminBookingResponse,
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
    response_model=PaginatedAdminBookingResponse,
    dependencies=[Depends(GroupDependency(ADMIN_GROUP_NAME))],
)
async def get_all_bookings(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        20,
        ge=1,
        le=MAX_PAGINATION_LIMIT,
        description="Maximum number of records to return",
    ),
    session: Session = Depends(get_session),
):
    """
    Get paginated bookings with user information for admin dashboard.

    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 20, max: 100)

    Returns:
        Paginated list of bookings with associated user data
    """
    logger.info(
        f"Fetching bookings for admin dashboard with skip={skip}, limit={limit}"
    )

    try:
        bookings = get_all_bookings_paginated(session, skip=skip, limit=limit)
        total = get_all_bookings_count(session)

        items = []
        for booking in bookings:
            items.append(
                AdminBookingResponse(
                    id=booking.id,
                    flight_order_id=booking.flight_order_id,
                    status=booking.status,
                    created_at=booking.created_at,
                    ticket_url=booking.ticket_url,
                    user={
                        "id": booking.user.id,
                        "email": booking.user.email,
                    },
                    amadeus_order_response=booking.amadeus_order_response,
                )
            )

        response = PaginatedAdminBookingResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

        logger.info(f"Successfully fetched {len(items)} bookings (total: {total})")
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
