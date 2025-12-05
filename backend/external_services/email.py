from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv
import os

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def send_email_async(subject: str, recipients: list[EmailStr], body_text: str):
    html = f"""
      <h2>{subject}</h2>
      <br/>
      <p>{body_text}</p>
      <br/>
      <br/>
      <br/>
      <p>Best regards</p>
      <p>Aero Bound Ventures Team</p>
   """
    message = MessageSchema(
        subject=subject, recipients=recipients, body=html, subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_password_reset_email(email: EmailStr, reset_token: str):
    """Send password reset email with reset link."""
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    reset_link = f"{frontend_url}/auth/reset-password?token={reset_token}"

    subject = "Password Reset Request - Aero Bound Ventures"
    recipients = [email]

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #333;">Password Reset Request</h2>
        <p>Hello,</p>
        <p>We received a request to reset your password for your Aero Bound Ventures account.</p>
        <p>Click the button below to reset your password:</p>
        <div style="margin: 30px 0;">
            <a href="{reset_link}" 
               style="background-color: #007bff; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 4px; display: inline-block;">
                Reset Password
            </a>
        </div>
        <p>Or copy and paste this link into your browser:</p>
        <p style="color: #007bff; word-break: break-all;">{reset_link}</p>
        <p style="color: #666; font-size: 14px; margin-top: 30px;">
            This link will expire in 1 hour for security reasons.
        </p>
        <p style="color: #666; font-size: 14px;">
            If you didn't request a password reset, please ignore this email or contact support if you have concerns.
        </p>
        <br/>
        <p>Best regards,</p>
        <p><strong>Aero Bound Ventures Team</strong></p>
    </div>
    """

    message = MessageSchema(
        subject=subject, recipients=recipients, body=html, subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_welcome_email(email: EmailStr):
    """Send welcome email to new user."""
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    subject = "Welcome to Aero Bound Ventures! ✈️"
    recipients = [email]

    # Read the HTML template
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "templates", "welcome_email.html"
    )
    with open(template_path, "r", encoding="utf-8") as file:
        html = file.read()

    # Replace placeholders with actual values
    html = html.replace("{{frontend_url}}", frontend_url)

    message = MessageSchema(
        subject=subject, recipients=recipients, body=html, subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)
