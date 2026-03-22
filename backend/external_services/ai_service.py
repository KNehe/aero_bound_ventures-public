"""
AI Service for personalized email content generation.

Uses Google Gemini (gemini-1.5-flash) to generate personalized greetings
and messages for transactional emails. Falls back to static default text
when the API key is missing, the API is unavailable, or a timeout occurs.
"""

import asyncio
import html
import os

from google import genai
from google.genai import types
from dotenv import load_dotenv

from backend.utils.log_manager import get_app_logger

load_dotenv()

logger = get_app_logger(__name__)

AI_TIMEOUT_SECONDS = 10

_api_key = os.getenv("GEMINI_API_KEY")
_client: genai.Client | None = None

if _api_key:
    try:
        _client = genai.Client(api_key=_api_key)
        logger.info("Gemini AI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
else:
    logger.warning(
        "GEMINI_API_KEY is not set. AI personalization will use fallback text."
    )


async def generate_personalized_greeting(prompt: str, fallback: str) -> str:
    """
    Generate a personalized greeting/message using Gemini.

    Args:
        prompt: The text prompt to send to the AI model.
        fallback: Default text returned if the AI call fails or is unavailable.

    Returns:
        The AI-generated text (HTML-escaped), or the fallback string.
    """
    if not _client:
        return fallback

    try:
        response = await asyncio.wait_for(
            _client.aio.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=200,
                ),
            ),
            timeout=AI_TIMEOUT_SECONDS,
        )
        if response.text:
            return html.escape(response.text.strip())
        return fallback
    except asyncio.TimeoutError:
        logger.warning(
            f"Gemini API timed out after {AI_TIMEOUT_SECONDS}s. Using fallback text."
        )
        return fallback
    except Exception as e:
        logger.error(f"Error generating AI message: {e}")
        return fallback


async def get_welcome_message() -> str:
    """Generate a personalized welcome message for a new user."""
    fallback = (
        "Thank you for joining <strong>Aero Bound Ventures</strong>! "
        "We're thrilled to have you on board and can't wait to help you "
        "explore the world."
    )
    prompt = (
        "Write a 2-sentence enthusiastic welcome message for a new user "
        "joining 'Aero Bound Ventures', a flight booking platform. "
        "Make it sound human, premium, and welcoming. "
        "Don't include subject lines, signatures, or greetings like 'Hi'."
    )
    return await generate_personalized_greeting(prompt, fallback)


async def get_password_reset_message() -> str:
    """Generate a personalized password reset acknowledgment message."""
    fallback = (
        "We received a request to reset your password for your "
        "Aero Bound Ventures account."
    )
    prompt = (
        "Write a 1-sentence helpful and polite message acknowledging a "
        "password reset request for a flight booking platform called "
        "'Aero Bound Ventures'. Keep it brief. "
        "Don't include subject lines, signatures, or greetings like 'Hi'."
    )
    return await generate_personalized_greeting(prompt, fallback)


async def get_booking_confirmation_message(pnr: str) -> str:
    """Generate a personalized booking confirmation message."""
    fallback = "Thank you for your order! Your booking has been successfully confirmed."
    prompt = (
        f"Write a 2-sentence enthusiastic thank you note for a customer "
        f"who just booked a flight with PNR '{pnr}' on a platform called "
        f"'Aero Bound Ventures'. "
        "Make it sound human, premium, and welcoming. "
        "Don't include subject lines, signatures, or greetings like 'Hi'."
    )
    return await generate_personalized_greeting(prompt, fallback)


async def get_booking_cancellation_message(pnr: str) -> str:
    """Generate a personalized booking cancellation message."""
    fallback = "Your booking has been successfully cancelled."
    prompt = (
        f"Write a 2-sentence polite and empathetic confirmation that a "
        f"flight booking (PNR '{pnr}') has been cancelled on a platform "
        f"called 'Aero Bound Ventures'. "
        "Don't include subject lines, signatures, or greetings like 'Hi'."
    )
    return await generate_personalized_greeting(prompt, fallback)


async def get_payment_success_message(pnr: str) -> str:
    """Generate a personalized payment success message for a customer."""
    fallback = (
        "Thank you for your payment. Your transaction has been processed "
        "and your booking is now confirmed."
    )
    prompt = (
        f"Write a 1-sentence enthusiastic thank you note for a customer "
        f"whose payment was successfully processed for a flight booking (PNR '{pnr}') "
        f"on a platform called 'Aero Bound Ventures'. "
        "Make it sound human, premium, and welcoming. "
        "Don't include subject lines, signatures, or greetings like 'Hi'."
    )
    return await generate_personalized_greeting(prompt, fallback)


async def get_admin_payment_message(pnr: str, email: str) -> str:
    """Generate a summary message for admins about a successful payment."""
    fallback = (
        f"A payment has been successfully completed for booking {pnr} by {email}."
    )
    prompt = (
        f"Write a 1-sentence analytical alert message for an administrator "
        f"confirming that a payment was successfully processed for booking PNR '{pnr}' "
        f"by customer '{email}' on 'Aero Bound Ventures'. "
        "Keep it professional and concise."
        "Don't include subject lines, signatures, or greetings like 'Hi'."
    )
    return await generate_personalized_greeting(prompt, fallback)


async def get_ticket_upload_message(pnr: str) -> str:
    """Generate a personalized ticket upload success message for a customer."""
    fallback = "Your ticket has been successfully uploaded and is now available in your account."
    prompt = (
        f"Write a 1-sentence polite and helpful notification informing a customer "
        f"that their flight ticket for PNR '{pnr}' has been successfully uploaded "
        f"and is ready for viewing on 'Aero Bound Ventures'. "
        "Make it sound premium and reassuring."
        "Don't include subject lines, signatures, or greetings like 'Hi'."
    )
    return await generate_personalized_greeting(prompt, fallback)


async def get_admin_order_message(pnr: str, email: str) -> str:
    """Generate a summary message for admins about a new booking order."""
    fallback = f"A new booking order has been placed for {pnr} by {email}."
    prompt = (
        f"Write a 1-sentence prompt alert for an administrator "
        f"notifying them that a new booking order has been placed for PNR '{pnr}' "
        f"by customer '{email}' on 'Aero Bound Ventures'. "
        "Keep it professional and action-oriented."
        "Don't include subject lines, signatures, or greetings like 'Hi'."
    )
    return await generate_personalized_greeting(prompt, fallback)


async def get_admin_cancellation_message(pnr: str, email: str) -> str:
    """Generate a summary message for admins about a booking cancellation."""
    fallback = f"A booking has been cancelled for {pnr} by {email}."
    prompt = (
        f"Write a 1-sentence alert for an administrator "
        f"notifying them that a booking for PNR '{pnr}' has been cancelled "
        f"by customer '{email}' on 'Aero Bound Ventures'. "
        "Include a reminder to review or process any applicable refunds."
        "Don't include subject lines, signatures, or greetings like 'Hi'."
    )
    return await generate_personalized_greeting(prompt, fallback)
