from pydantic import BaseModel, EmailStr
import uuid


class BaseEvent(BaseModel):
    event_type: str


class BookingCreatedEvent(BaseEvent):
    booking_id: uuid.UUID
    user_id: uuid.UUID
    user_email: EmailStr
    pnr: str


class PaymentSuccessEvent(BaseEvent):
    booking_id: uuid.UUID
    user_id: uuid.UUID
    user_email: EmailStr
    pnr: str


class PaymentFailedEvent(BaseEvent):
    booking_id: uuid.UUID
    user_id: uuid.UUID
    pnr: str
    reason: str = "Unknown error"


class TicketUploadedEvent(BaseEvent):
    booking_id: uuid.UUID
    user_id: uuid.UUID
    user_email: EmailStr
    pnr: str


class UserRegisteredEvent(BaseEvent):
    email: EmailStr
    user_id: uuid.UUID


class PasswordResetRequestedEvent(BaseEvent):
    email: EmailStr
    reset_token: str
