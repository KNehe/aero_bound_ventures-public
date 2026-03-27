from pydantic import BaseModel


class TicketUploadResponse(BaseModel):
    message: str
    ticket_url: str
    booking_id: str
    public_id: str