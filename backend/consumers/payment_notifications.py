from backend.utils.log_manager import get_app_logger
from backend.schemas.events import PaymentSuccessEvent, PaymentFailedEvent


from backend.external_services.email import send_email
from backend.crud.users import get_admin_emails
from backend.models.notifications import NotificationType
from backend.utils.notification_service import create_and_publish_notification
from backend.utils.constants import KafkaEventTypes

from backend.crud.database import engine
from sqlmodel import Session

logger = get_app_logger(__name__)


async def process_payment_notifications(message: dict):
    """Handler for payment.events topic"""
    try:
        event_type = message.get("event_type")
        logger.info(f"Processing payment event: {event_type}")

        with Session(engine) as session:
            if event_type == KafkaEventTypes.PAYMENT_SUCCESSFUL:
                event = PaymentSuccessEvent(**message)
                await _handle_payment_success(session, event)
            elif event_type == KafkaEventTypes.PAYMENT_FAILED:
                event = PaymentFailedEvent(**message)
                await _handle_payment_failure(session, event)
            else:
                logger.warning(f"Unknown payment event type: {event_type}")

    except Exception as e:
        logger.error(f"Failed to process payment event: {e}")


async def _handle_payment_success(session, event: PaymentSuccessEvent):
    # 1. Send Customer Email
    if event.user_email:
        try:
            await send_email(
                recipients=[event.user_email],
                subject="Payment Successful : Aero Bound Ventures",
                template_name="payment_success.html",
                extra={
                    "pnr": event.pnr,
                    "booking_id": str(event.booking_id),
                },
            )
            logger.info(f"Payment success email sent to {event.user_email}")
        except Exception as e:
            logger.error(f"Failed to send payment success email: {e}")

    # 2. Notify Admins
    admin_emails = get_admin_emails(session)
    if admin_emails:
        try:
            await send_email(
                recipients=admin_emails,
                subject="[ADMIN] Payment Completed for Booking",
                template_name="admin_payment_notification.html",
                extra={
                    "pnr": event.pnr,
                    "user_email": event.user_email,
                    "booking_id": str(event.booking_id),
                },
            )
            logger.info(
                f"Admin payment notification sent to {len(admin_emails)} admins"
            )
        except Exception as e:
            logger.error(f"Failed to send admin payment notification email: {e}")

    # 3. In-App Notification
    if event.user_id:
        try:
            await create_and_publish_notification(
                db=session,
                user_id=event.user_id,
                message=f"Payment successful for flight with PNR {event.pnr}",
                notification_type=NotificationType.PAYMENT_SUCCESS,
            )
        except Exception as e:
            logger.error(f"Failed to create success in-app notification: {e}")


async def _handle_payment_failure(session, event: PaymentFailedEvent):
    # In-App Notification for Failure
    if event.user_id:
        try:
            await create_and_publish_notification(
                db=session,
                user_id=event.user_id,
                message=f"Payment failed for flight with PNR {event.pnr}. Reason: {event.reason}",
                notification_type=NotificationType.PAYMENT_FAILED,
            )
            logger.info(
                f"Payment failure notification created for user {event.user_id}"
            )
        except Exception as e:
            logger.error(f"Failed to create failure in-app notification: {e}")
