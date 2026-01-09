from backend.utils.log_manager import get_app_logger
from backend.schemas.events import (
    UserRegisteredEvent,
    PasswordResetRequestedEvent,
    PasswordChangedEvent,
)


from backend.external_services.email import (
    send_welcome_email,
    send_password_reset_email,
    send_email,
)
from backend.utils.constants import KafkaEventTypes

logger = get_app_logger(__name__)


async def process_user_notifications(message: dict):
    """Handler for user.events topic"""
    try:
        event_type = message.get("event_type")
        logger.info(f"Processing user event: {event_type}")

        if event_type == KafkaEventTypes.USER_REGISTERED:
            event = UserRegisteredEvent(**message)
            await send_welcome_email(event.email)
            logger.info(f"Welcome email sent to {event.email}")

        elif event_type == KafkaEventTypes.PASSWORD_RESET_REQUESTED:
            event = PasswordResetRequestedEvent(**message)
            try:
                await send_password_reset_email(event.email, event.reset_token)
                logger.info(f"Password reset email sent to {event.email}")
            except Exception as e:
                logger.error(f"Failed to send password reset email: {e}")

        elif event_type == KafkaEventTypes.PASSWORD_CHANGED:
            event = PasswordChangedEvent(**message)
            try:
                await send_email(
                    recipients=[event.email],
                    subject="Password Changed - Aero Bound Ventures",
                    template_name="password_changed.html",
                    extra={},
                )
                logger.info(f"Password changed notification sent to {event.email}")
            except Exception as e:
                logger.error(f"Failed to send password changed email: {e}")

        else:
            logger.warning(f"Unknown event type: {event_type}")

    except Exception as e:
        logger.error(f"Failed to process user event: {e}")
