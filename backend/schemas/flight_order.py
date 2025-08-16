from pydantic import BaseModel


class FlightOrderRequestBody(BaseModel):
    originLocationCode: str
    destinationLocationCode: str
    departureDate: str
    returnDate: str | None = None
    adults: int
    travelers: list
