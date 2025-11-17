from sqlmodel import SQLModel
import uuid


class BookingResponse(SQLModel):
    id: uuid.UUID
    flight_order_id: str
    status: str
