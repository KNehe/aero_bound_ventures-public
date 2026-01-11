"""CRUD operations for bookings"""

import uuid
from sqlmodel import Session, select, func
from backend.models.bookings import Booking


MAX_PAGINATION_LIMIT = 100


def get_user_bookings_paginated(
    session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 20
) -> list[Booking]:
    """
    Get paginated bookings for a user

    Args:
        session: Database session
        user_id: User ID to filter bookings
        skip: Number of records to skip
        limit: Maximum number of records to return (capped at MAX_PAGINATION_LIMIT)

    Returns:
        List of Booking objects
    """
    limit = min(limit, MAX_PAGINATION_LIMIT)
    statement = (
        select(Booking)
        .where(Booking.user_id == user_id)
        .order_by(Booking.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_user_bookings_count(session: Session, user_id: uuid.UUID) -> int:
    """
    Get total count of bookings for a user

    Args:
        session: Database session
        user_id: User ID to filter bookings

    Returns:
        Total count of bookings
    """
    statement = (
        select(func.count()).select_from(Booking).where(Booking.user_id == user_id)
    )
    return session.exec(statement).one()


def get_all_bookings_paginated(
    session: Session, skip: int = 0, limit: int = 20
) -> list[Booking]:
    """
    Get all bookings with pagination (for admin)

    Args:
        session: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return (capped at MAX_PAGINATION_LIMIT)

    Returns:
        List of Booking objects
    """
    limit = min(limit, MAX_PAGINATION_LIMIT)
    statement = (
        select(Booking).order_by(Booking.created_at.desc()).offset(skip).limit(limit)
    )
    return list(session.exec(statement).all())


def get_all_bookings_count(session: Session) -> int:
    """
    Get total count of all bookings

    Args:
        session: Database session

    Returns:
        Total count of bookings
    """
    statement = select(func.count()).select_from(Booking)
    return session.exec(statement).one()


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
