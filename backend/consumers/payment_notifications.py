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


async def process_payment_notifications(message: dict):
    """Handler for payment.events topic"""
    event_type = message.get("event_type")
    booking_id = message.get("booking_id")
    user_id = message.get("user_id")
    pnr = message.get("pnr")
    user_email = message.get("user_email")

    if not all([event_type, booking_id]):
        logger.warning(f"Received payment event {event_type} with missing data")
        return

    logger.info(f"Processing payment event: {event_type} for booking {booking_id}")

    try:
        with Session(engine) as session:
            if event_type == KafkaEvents.PAYMENT_SUCCESSFUL:
                await _handle_payment_success(
                    session, booking_id, pnr, user_email, user_id
                )
            elif event_type == KafkaEvents.PAYMENT_FAILED:
                reason = message.get("reason", "Unknown")
                await _handle_payment_failure(session, pnr, user_id, reason)
            else:
                logger.warning(f"Unknown payment event type: {event_type}")

    except Exception as e:
        logger.error(f"Failed to process payment event {event_type}: {e}")


async def _handle_payment_success(session, booking_id, pnr, user_email, user_id):
    # 1. Send Customer Email
    if user_email:
        await send_email(
            recipients=[user_email],
            subject="Payment Successful : Aero Bound Ventures",
            template_name="payment_success.html",
            extra={
                "pnr": pnr,
                "booking_id": booking_id,
            },
        )
        logger.info(f"Payment success email sent to {user_email}")

    # 2. Notify Admins
    admin_emails = get_admin_emails(session)
    if admin_emails:
        await send_email(
            recipients=admin_emails,
            subject="[ADMIN] Payment Completed for Booking",
            template_name="admin_payment_notification.html",
            extra={
                "pnr": pnr,
                "user_email": user_email,
                "booking_id": booking_id,
            },
        )
        logger.info(f"Admin payment notification sent to {len(admin_emails)} admins")

    # 3. In-App Notification
    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
            await create_and_publish_notification(
                db=session,
                user_id=user_uuid,
                message=f"Payment successful for flight with PNR {pnr}",
                notification_type=NotificationType.PAYMENT_SUCCESS,
            )
        except Exception as e:
            logger.error(f"Failed to create success in-app notification: {e}")


async def _handle_payment_failure(session, pnr, user_id, reason):
    # In-App Notification for Failure
    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
            await create_and_publish_notification(
                db=session,
                user_id=user_uuid,
                message=f"Payment failed for flight with PNR {pnr}. Please try again.",
                notification_type=NotificationType.PAYMENT_FAILED,
            )
            logger.info(f"Payment failure notification created for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to create failure in-app notification: {e}")
