import logging
from backend.external_services.email import send_welcome_email, send_password_reset_email

logger = logging.getLogger(__name__)

async def process_user_notifications(message: dict):
    """Handler for user.events topic"""
    event_type = message.get("event_type")
    email = message.get("email")

    if not email:
        logger.warning("Received user event without email")
        return

    logger.info(f"Processing user event: {event_type} for {email}")

    try:
        if event_type == "user_registered":
            await send_welcome_email(email)
            logger.info(f"Welcome email sent to {email}")
        
        elif event_type == "password_reset_requested":
            reset_token = message.get("reset_token")
            if reset_token:
                await send_password_reset_email(email, reset_token)
                logger.info(f"Password reset email sent to {email}")
            else:
                logger.warning("Password reset requested without token")
        
        else:
            logger.warning(f"Unknown event type: {event_type}")

    except Exception as e:
        logger.error(f"Failed to process user event {event_type}: {e}")

