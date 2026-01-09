from backend.utils.log_manager import get_app_logger
from backend.schemas.events import BookingCreatedEvent, BookingCancelledEvent


from backend.external_services.email import send_email
from backend.crud.users import get_admin_emails, get_admin_users
from backend.models.notifications import NotificationType
from backend.utils.notification_service import create_and_publish_notification
from backend.utils.constants import KafkaEventTypes

from backend.crud.database import engine
from sqlmodel import Session

logger = get_app_logger(__name__)


async def process_booking_notifications(message: dict):
    """Handler for booking.events topic"""
    try:
        event_type = message.get("event_type")

        logger.info(f"Processing booking event: {event_type}")

        if event_type == KafkaEventTypes.BOOKING_CREATED:
            event = BookingCreatedEvent(**message)
            await _handle_booking_created(event)
        elif event_type == KafkaEventTypes.BOOKING_CANCELLED:
            event = BookingCancelledEvent(**message)
            await _handle_booking_cancelled(event)
        else:
            logger.warning(f"Unknown booking event type: {event_type}")

    except Exception as e:
        logger.error(f"Failed to process booking event: {e}")


async def _handle_booking_created(event: BookingCreatedEvent):
    # 1. Send Customer Confirmation Email
    try:
        await send_email(
            recipients=[event.user_email],
            subject="Your Booking Order Received : Aero Bound Ventures",
            template_name="order_confirmation.html",
            extra={
                "pnr": event.pnr,
                "booking_id": str(event.booking_id),
            },
        )
        logger.info(f"Booking confirmation email sent to {event.user_email}")
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email: {e}")

    # 2. Notify Admins
    with Session(engine) as session:
        admin_emails = get_admin_emails(session)
        if admin_emails:
            try:
                await send_email(
                    recipients=admin_emails,
                    subject="[ADMIN] New Booking Order Placed",
                    template_name="admin_order_notification.html",
                    extra={
                        "pnr": event.pnr,
                        "user_email": event.user_email,
                        "booking_id": str(event.booking_id),
                    },
                )
                logger.info(
                    f"Admin notification email sent to {len(admin_emails)} admins"
                )
            except Exception as e:
                logger.error(f"Failed to send admin notification email: {e}")

        # 3. Create In-App Notification (if user_id provided)
        if event.user_id:
            try:
                await create_and_publish_notification(
                    db=session,
                    user_id=event.user_id,
                    message=f"Your flight booking has been confirmed. PNR: {event.pnr}",
                    notification_type=NotificationType.BOOKING_CONFIRMED,
                )
                logger.info("In-app notification created for booking confirmation")
            except Exception as e:
                logger.error(
                    f"Failed to create inside consumer in-app notification: {e}"
                )


async def _handle_booking_cancelled(event: BookingCancelledEvent):
    """Handle booking cancelled event - send cancellation confirmation email to user and admins"""
    pnr_display = event.pnr or "N/A"

    # 1. Send Customer Cancellation Confirmation Email
    try:
        await send_email(
            recipients=[event.user_email],
            subject=f"Booking Cancellation Confirmed - {pnr_display}",
            template_name="booking_cancellation.html",
            extra={
                "pnr": pnr_display,
                "booking_id": str(event.booking_id),
            },
        )
        logger.info(f"Booking cancellation email sent to {event.user_email}")
    except Exception as e:
        logger.error(f"Failed to send booking cancellation email: {e}")

    # 2. Notify Admins
    with Session(engine) as session:
        admin_emails = get_admin_emails(session)
        if admin_emails:
            try:
                await send_email(
                    recipients=admin_emails,
                    subject=f"[ADMIN] Booking Cancelled - {pnr_display}",
                    template_name="admin_booking_cancellation.html",
                    extra={
                        "pnr": pnr_display,
                        "user_email": event.user_email,
                        "booking_id": str(event.booking_id),
                    },
                )
                logger.info(
                    f"Admin cancellation notification sent to {len(admin_emails)} admins"
                )
            except Exception as e:
                logger.error(f"Failed to send admin cancellation notification: {e}")

        # 3. Create In-App Notification for user
        if event.user_id:
            try:
                await create_and_publish_notification(
                    db=session,
                    user_id=event.user_id,
                    message=f"Your booking has been cancelled. PNR: {pnr_display}",
                    notification_type=NotificationType.BOOKING_CANCELLED,
                )
                logger.info("In-app notification created for booking cancellation")
            except Exception as e:
                logger.error(
                    f"Failed to create in-app notification for cancellation: {e}"
                )

        # 4. Create In-App Notifications for admins
        admin_users = get_admin_users(session)
        for admin in admin_users:
            try:
                await create_and_publish_notification(
                    db=session,
                    user_id=admin.id,
                    message=f"Booking cancelled by {event.user_email}. PNR: {pnr_display}",
                    notification_type=NotificationType.BOOKING_CANCELLED,
                )
            except Exception as e:
                logger.error(f"Failed to create admin in-app notification: {e}")
        if admin_users:
            logger.info(f"In-app notifications created for {len(admin_users)} admins")
