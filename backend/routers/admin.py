from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, timedelta
from backend.crud.database import get_session
from backend.models.bookings import Booking
from backend.models.constants import ADMIN_GROUP_NAME
from backend.schemas.admin import BookingStatsResponse, AdminBookingResponse
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
        # Get all bookings
        bookings = session.exec(select(Booking)).all()

        # Calculate total bookings
        total_bookings = len(bookings)

        # Calculate total revenue
        total_revenue = 0.0
        for booking in bookings:
            if booking.amadeus_order_response:
                travelers_pricing = booking.amadeus_order_response.get("travelers", [])
                for traveler in travelers_pricing:
                    price_info = traveler.get("price", {})
                    total_str = price_info.get("total", "0")
                    try:
                        total_revenue += float(total_str)
                    except (ValueError, TypeError):
                        continue

        # Calculate active users (unique users who have made bookings)
        unique_user_ids = set(booking.user_id for booking in bookings)
        active_users = len(unique_user_ids)

        # Calculate bookings today
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
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
    response_model=list[AdminBookingResponse],
    dependencies=[Depends(GroupDependency(ADMIN_GROUP_NAME))],
)
async def get_all_bookings(
    session: Session = Depends(get_session),
):
    """
    Get all bookings with user information for admin dashboard.

    Returns:
        List of all bookings with associated user data
    """
    logger.info("Fetching all bookings for admin dashboard")

    try:
        bookings = session.exec(
            select(Booking).order_by(Booking.created_at.desc())
        ).all()

        response = []
        for booking in bookings:
            response.append(
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

        logger.info(f"Successfully fetched {len(response)} bookings")
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
