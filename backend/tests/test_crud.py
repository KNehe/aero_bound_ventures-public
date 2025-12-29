from backend.crud.users import create_user, get_user_by_email
from sqlmodel import Session
from backend.models.bookings import Booking
from backend.crud.bookings import (
    create_booking,
    update_booking_status,
    get_booking_by_id,
)
from backend.crud.notifications import (
    create_notification,
    get_notifications_by_user,
    mark_notification_as_read,
)
from backend.models.notifications import Notification, NotificationType
from backend.schemas.notifications import NotificationCreate


def test_create_user(session: Session):
    email = "test@example.com"
    password = "securepassword"
    user = create_user(session, email=email, password=password)

    assert user.email == email
    assert user.id is not None

    db_user = get_user_by_email(session, email=email)
    assert db_user.id == user.id


def test_create_booking(session: Session):
    user = create_user(session, "booker@example.com", "pass")

    booking_in = Booking(
        user_id=user.id,
        flight_order_id="FLIGHT_123",
        total_price=500.0,
        currency="USD",
        status="pending",
        amadeus_order_response={},
    )
    booking = create_booking(session, booking_in)

    assert booking.id is not None
    assert booking.user_id == user.id

    db_booking = get_booking_by_id(session, booking.id)
    assert db_booking.id == booking.id
    assert db_booking.status == "pending"


def test_update_booking_status(session: Session):
    user = create_user(session, "updater@example.com", "pass")
    booking_in = Booking(
        user_id=user.id,
        flight_order_id="FLIGHT_456",
        total_price=600.0,
        currency="USD",
        status="pending",
        amadeus_order_response={},
    )

    booking = create_booking(session, booking_in)
    updated_booking = update_booking_status(session, booking.id, "confirmed")
    assert updated_booking.status == "confirmed"

    db_booking = get_booking_by_id(session, booking.id)
    assert db_booking.status == "confirmed"


def test_notifications_crud(session: Session):
    user = create_user(session, "notify@example.com", "pass")

    notify_in = NotificationCreate(
        user_id=user.id, type=NotificationType.GENERAL, message="Test alert"
    )
    notification = create_notification(session, notify_in)

    assert notification.id is not None
    assert notification.user_id == user.id
    assert notification.is_read is False

    notifs = get_notifications_by_user(session, user.id)
    assert len(notifs) == 1
    assert notifs[0].id == notification.id

    mark_notification_as_read(session, notification.id, user.id)

    db_notif = session.get(Notification, notification.id)
    assert db_notif.is_read is True
