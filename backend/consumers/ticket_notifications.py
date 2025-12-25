import logging
import uuid
from sqlmodel import Session
from backend.crud.database import engine
from backend.external_services.email import send_email
from backend.crud.users import get_admin_users
from backend.models.notifications import NotificationType
from backend.models.kafka_topics import KafkaEvents
from backend.utils.notification_service import create_and_publish_notification

logger = logging.getLogger(__name__)


async def process_ticket_notifications(message: dict):
    """Handler for ticket.events topic"""
    event_type = message.get("event_type")
    pnr = message.get("pnr")
    booking_id = message.get("booking_id")
    user_id = message.get("user_id")
    user_email = message.get("user_email")
    # ticket_url = message.get("ticket_url")

    if not all([event_type, pnr, booking_id, user_id]):
        logger.warning("Received ticket event with missing data")
        return

    logger.info(f"Processing ticket event: {event_type} for booking {booking_id}")

    try:
        if event_type == KafkaEvents.TICKET_UPLOADED:
            await _handle_ticket_uploaded(pnr, booking_id, user_id, user_email)
        else:
            logger.warning(f"Unknown ticket event type: {event_type}")

    except Exception as e:
        logger.error(f"Failed to process ticket event {event_type}: {e}")


async def _handle_ticket_uploaded(pnr, booking_id, user_id, user_email):
    # 1. Send Email to User
    if user_email:
        await send_email(
            recipients=[user_email],
            subject="Ticket Uploaded Successfully : Aero Bound Ventures",
            template_name="ticket_upload_success.html",
            extra={
                "pnr": pnr,
                "booking_id": booking_id,
            },
        )
        logger.info(f"Ticket upload email sent to {user_email}")

    with Session(engine) as session:
        # 2. In-App Notification for User
        try:
            user_uuid = uuid.UUID(user_id)
            await create_and_publish_notification(
                db=session,
                user_id=user_uuid,
                message=f"Your ticket for flight with PNR: {pnr} has been uploaded successfully.",
                notification_type=NotificationType.TICKET_UPLOADED,
            )
        except Exception as e:
            logger.error(f"Failed to send user in-app notification: {e}")

        # 3. In-App Notifications for Admins
        try:
            admin_users = get_admin_users(session)
            for admin in admin_users:
                await create_and_publish_notification(
                    db=session,
                    user_id=admin.id,
                    message=f"Ticket uploaded for flight with PNR: {pnr}.",
                    notification_type=NotificationType.TICKET_UPLOADED,
                )
            logger.info("Admin in-app notifications sent for ticket upload")
        except Exception as e:
            logger.error(f"Failed to send admin in-app notifications: {e}")
