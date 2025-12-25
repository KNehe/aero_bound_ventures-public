import logging
import uuid
from sqlmodel import Session
from backend.crud.database import engine
from backend.external_services.email import send_email
from backend.crud.users import get_admin_emails
from backend.models.notifications import NotificationType
from backend.models.kafka_topics import KafkaEvents
from backend.utils.notification_service import create_and_publish_notification

logger = logging.getLogger(__name__)


async def process_booking_notifications(message: dict):
    """Handler for booking.events topic"""
    event_type = message.get("event_type")
    booking_id = message.get("booking_id")
    user_id = message.get("user_id")
    pnr = message.get("pnr")
    user_email = message.get("user_email")

    if not all([event_type, booking_id, user_email]):
        logger.warning("Received booking event with missing data")
        return

    logger.info(f"Processing booking event: {event_type} for booking {booking_id}")

    try:
        if event_type == KafkaEvents.BOOKING_CREATED:
            await _handle_booking_created(booking_id, pnr, user_email, user_id)
        else:
            logger.warning(f"Unknown booking event type: {event_type}")

    except Exception as e:
        logger.error(f"Failed to process booking event {event_type}: {e}")


async def _handle_booking_created(booking_id, pnr, user_email, user_id):
    # 1. Send Customer Confirmation Email
    await send_email(
        recipients=[user_email],
        subject="Your Booking Order Received : Aero Bound Ventures",
        template_name="order_confirmation.html",
        extra={
            "pnr": pnr,
            "booking_id": booking_id,
        },
    )
    logger.info(f"Booking confirmation email sent to {user_email}")

    # 2. Notify Admins
    with Session(engine) as session:
        admin_emails = get_admin_emails(session)
        if admin_emails:
            await send_email(
                recipients=admin_emails,
                subject="[ADMIN] New Booking Order Placed",
                template_name="admin_order_notification.html",
                extra={
                    "pnr": pnr,
                    "user_email": user_email,
                    "booking_id": booking_id,
                },
            )
            logger.info(f"Admin notification email sent to {len(admin_emails)} admins")

        # 3. Create In-App Notification (if user_id provided)
        if user_id:
            try:
                user_uuid = uuid.UUID(user_id)
                await create_and_publish_notification(
                    db=session,
                    user_id=user_uuid,
                    message=f"Your flight booking has been confirmed. PNR: {pnr}",
                    notification_type=NotificationType.BOOKING_CONFIRMED,
                )
                logger.info("In-app notification created for booking confirmation")
            except Exception as e:
                logger.error(
                    f"Failed to create inside consumer in-app notification: {e}"
                )
