"""CRUD operations for bookings"""

import uuid
from sqlmodel import Session, select
from backend.models.bookings import Booking
from backend.utils.pagination import (
    CursorPaginator,
    get_total_count,
)

MAX_PAGINATION_LIMIT = 100


def _booking_cursor_fields(booking: Booking) -> dict:
    """Extract cursor fields from a booking."""
    return {"created_at": booking.created_at, "id": booking.id}


def get_user_bookings_cursor(
    session: Session,
    user_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = 20,
    include_count: bool = False,
) -> tuple[list[Booking], str | None, bool, int | None]:
    """
    Get cursor-paginated bookings for a user.

    Args:
        session: Database session
        user_id: User ID to filter bookings
        cursor: Cursor for pagination (None for first page)
        limit: Maximum number of records to return (capped at MAX_PAGINATION_LIMIT)
        include_count: Whether to include total count (can be expensive)

    Returns:
        Tuple of (list of Booking objects, next_cursor or None, has_more, total_count or None)
    """
    paginator = CursorPaginator(
        cursor=cursor,
        limit=limit,
        order_fields=["created_at", "id"],
        order_direction="desc",
    )

    # Build base query
    query = select(Booking).where(Booking.user_id == user_id)

    # Get total count if requested (before applying cursor/limit)
    total_count = None
    if include_count:
        count_query = select(Booking).where(Booking.user_id == user_id)
        total_count = get_total_count(session, count_query)

    # Apply pagination
    query = paginator.apply_cursor_filter(query, Booking)
    query = paginator.apply_ordering(query, Booking)
    query = paginator.apply_limit(query)

    bookings = list(session.exec(query).all())
    items, next_cursor, has_more = paginator.build_result(
        bookings, _booking_cursor_fields
    )

    return items, next_cursor, has_more, total_count


def get_all_bookings_cursor(
    session: Session,
    cursor: str | None = None,
    limit: int = 20,
    include_count: bool = False,
) -> tuple[list[Booking], str | None, bool, int | None]:
    """
    Get cursor-paginated bookings (admin view).

    Args:
        session: Database session
        cursor: Cursor for pagination (None for first page)
        limit: Maximum number of records to return (capped at MAX_PAGINATION_LIMIT)
        include_count: Whether to include total count (can be expensive)

    Returns:
        Tuple of (list of Booking objects, next_cursor or None, has_more, total_count or None)
    """
    paginator = CursorPaginator(
        cursor=cursor,
        limit=limit,
        order_fields=["created_at", "id"],
        order_direction="desc",
    )

    # Build base query
    query = select(Booking)

    # Get total count if requested
    total_count = None
    if include_count:
        total_count = get_total_count(session, select(Booking))

    # Apply pagination
    query = paginator.apply_cursor_filter(query, Booking)
    query = paginator.apply_ordering(query, Booking)
    query = paginator.apply_limit(query)

    bookings = list(session.exec(query).all())
    items, next_cursor, has_more = paginator.build_result(
        bookings, _booking_cursor_fields
    )

    return items, next_cursor, has_more, total_count


def get_booking_by_id(session: Session, booking_id: str) -> Booking | None:
    """
    Get a booking by its ID

    Args:
        session: Database session
        booking_id: Booking ID to search for

    Returns:
        Booking object if found, None otherwise
    """
    statement = select(Booking).where(Booking.id == booking_id)
    booking = session.exec(statement).first()
    return booking


def create_booking(session: Session, booking: Booking) -> Booking:
    """
    Create a new booking

    Args:
        session: Database session
        booking: Booking object to create

    Returns:
        Created booking object
    """
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def update_booking_status(
    session: Session, booking_id: str, status: str
) -> Booking | None:
    """
    Update the status of a booking

    Args:
        session: Database session
        booking_id: Booking ID to update
        status: New status (e.g., 'pending', 'confirmed', 'cancelled')

    Returns:
        Updated booking object if found, None otherwise
    """
    booking = get_booking_by_id(session, booking_id)
    if booking:
        booking.status = status
        session.add(booking)
        session.commit()
        session.refresh(booking)
    return booking


def update_booking_ticket_url(
    session: Session, booking_id: str, ticket_url: str
) -> Booking | None:
    """
    Update the ticket URL of a booking

    Args:
        session: Database session
        booking_id: Booking ID to update
        ticket_url: URL of the uploaded ticket

    Returns:
        Updated booking object if found, None otherwise
    """
    booking = get_booking_by_id(session, booking_id)
    if booking:
        booking.ticket_url = ticket_url
        session.add(booking)
        session.commit()
        session.refresh(booking)
    return booking
