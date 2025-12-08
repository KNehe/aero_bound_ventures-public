"""CRUD operations for bookings"""

from sqlmodel import Session, select
from backend.models.bookings import Booking


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