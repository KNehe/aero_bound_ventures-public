from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from backend.application.admin.admin_bookings import (
    AdminBookingNotFound,
    AdminBookingRecord,
    AdminBookingStatsRecord,
    AdminBookingsPage,
    GetAdminBooking,
    GetAdminBookingStats,
    ListAdminBookings,
)
from backend.crud.database import get_session
from backend.infrastructure.admin.sqlmodel_admin_booking_repository import (
    SqlModelAdminBookingRepository,
)
from backend.models.constants import ADMIN_GROUP_NAME
from backend.schemas.admin import (
    AdminBookingResponse,
    BookingStatsResponse,
    CursorPaginatedAdminBookingResponse,
)
from backend.utils.dependencies import GroupDependency
from backend.utils.log_manager import get_app_logger
from backend.utils.pagination import MAX_PAGINATION_LIMIT

logger = get_app_logger(__name__)

router = APIRouter()


def get_admin_booking_stats_use_case(
    session: Session = Depends(get_session),
) -> GetAdminBookingStats:
    return GetAdminBookingStats(
        admin_booking_repository=SqlModelAdminBookingRepository(session),
    )


def get_list_admin_bookings_use_case(
    session: Session = Depends(get_session),
) -> ListAdminBookings:
    return ListAdminBookings(
        admin_booking_repository=SqlModelAdminBookingRepository(session),
    )


def get_admin_booking_use_case(
    session: Session = Depends(get_session),
) -> GetAdminBooking:
    return GetAdminBooking(
        admin_booking_repository=SqlModelAdminBookingRepository(session),
    )


def _to_booking_stats_response(
    stats: AdminBookingStatsRecord,
) -> BookingStatsResponse:
    return BookingStatsResponse(
        total_bookings=stats.total_bookings,
        total_revenue=stats.total_revenue,
        active_users=stats.active_users,
        bookings_today=stats.bookings_today,
        bookings_this_week=stats.bookings_this_week,
    )


def _to_admin_booking_response(
    booking: AdminBookingRecord,
) -> AdminBookingResponse:
    return AdminBookingResponse(
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


def _to_paginated_admin_booking_response(
    page: AdminBookingsPage,
) -> CursorPaginatedAdminBookingResponse:
    return CursorPaginatedAdminBookingResponse(
        items=[_to_admin_booking_response(booking) for booking in page.items],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
        has_previous=page.has_previous,
        total_count=page.total_count,
        limit=page.limit,
    )


@router.get(
    "/stats/bookings",
    response_model=BookingStatsResponse,
    dependencies=[Depends(GroupDependency(ADMIN_GROUP_NAME))],
)
async def get_booking_stats(
    admin_booking_stats_use_case: GetAdminBookingStats = Depends(
        get_admin_booking_stats_use_case
    ),
):
    """
    Get booking statistics for admin dashboard.
    """
    logger.info("Calculating booking statistics")

    try:
        stats = admin_booking_stats_use_case.execute()
        logger.info("Successfully calculated booking statistics")
        return _to_booking_stats_response(stats)
    except Exception:
        logger.exception("Error calculating booking statistics")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    list_admin_bookings_use_case: ListAdminBookings = Depends(
        get_list_admin_bookings_use_case
    ),
):
    """
    Get cursor-paginated bookings with user information for admin dashboard.
    """
    logger.info(
        f"Fetching bookings for admin dashboard with cursor={cursor}, limit={limit}"
    )

    try:
        page = list_admin_bookings_use_case.execute(
            cursor=cursor,
            limit=limit,
            include_count=include_count,
        )
        logger.info(
            f"Successfully fetched {len(page.items)} bookings (has_more: {page.has_more})"
        )
        return _to_paginated_admin_booking_response(page)
    except Exception:
        logger.exception("Error fetching bookings for admin")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching bookings",
        )


@router.get(
    "/bookings/{booking_id}",
    response_model=AdminBookingResponse,
    dependencies=[Depends(GroupDependency(ADMIN_GROUP_NAME))],
)
async def get_booking(
    booking_id: str,
    admin_booking_use_case: GetAdminBooking = Depends(get_admin_booking_use_case),
):
    """
    Get a single booking by ID for admin dashboard.
    """
    logger.info(f"Fetching booking {booking_id} for admin")

    try:
        booking = admin_booking_use_case.execute(booking_id=booking_id)
        logger.info(f"Successfully fetched booking {booking_id}")
        return _to_admin_booking_response(booking)
    except AdminBookingNotFound:
        logger.warning(f"Booking {booking_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    except Exception:
        logger.exception(f"Error fetching booking {booking_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching the booking",
        )
