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
