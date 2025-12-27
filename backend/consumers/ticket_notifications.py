from backend.utils.log_manager import get_app_logger
from backend.schemas.events import TicketUploadedEvent
from backend.external_services.email import send_email
from backend.crud.users import get_admin_users
from backend.models.notifications import NotificationType
from backend.utils.notification_service import create_and_publish_notification
from backend.utils.constants import KafkaEventTypes

from backend.crud.database import engine
from sqlmodel import Session

logger = get_app_logger(__name__)


async def process_ticket_notifications(message: dict):
    """Handler for ticket.events topic"""
    try:
        event_type = message.get("event_type")
        logger.info(f"Processing ticket event: {event_type}")

        if event_type == KafkaEventTypes.TICKET_UPLOADED:
            event = TicketUploadedEvent(**message)
            await _handle_ticket_uploaded(event)
        else:
            logger.warning(f"Unknown ticket event type: {event_type}")

    except Exception as e:
        logger.error(f"Failed to process ticket event: {e}")


async def _handle_ticket_uploaded(event: TicketUploadedEvent):
    # 1. Send Email to User
    if event.user_email:
        await send_email(
            recipients=[event.user_email],
            subject="Ticket Uploaded Successfully : Aero Bound Ventures",
            template_name="ticket_upload_success.html",
            extra={
                "pnr": event.pnr,
                "booking_id": event.booking_id,
            },
        )
        logger.info(f"Ticket upload email sent to {event.user_email}")

    with Session(engine) as session:
        # 2. In-App Notification for User
        if event.user_id:
            try:
                await create_and_publish_notification(
                    db=session,
                    user_id=event.user_id,
                    message=f"Your ticket for flight with PNR: {event.pnr} has been uploaded successfully.",
                    notification_type=NotificationType.TICKET_UPLOADED,
                )
                logger.info("In-app notification created for user for ticket upload")
            except Exception as e:
                logger.error(f"Failed to create user ticket upload notification: {e}")

        # 3. In-App Notifications for Admins
        try:
            admin_users = get_admin_users(session)
            for admin in admin_users:
                await create_and_publish_notification(
                    db=session,
                    user_id=admin.id,
                    message=f"Ticket uploaded for flight with PNR: {event.pnr}.",
                    notification_type=NotificationType.TICKET_UPLOADED,
                )
            logger.info(
                f"In-app notifications created for {len(admin_users)} admins for ticket upload"
            )
        except Exception as e:
            logger.error(f"Failed to create admin ticket upload notifications: {e}")
