from pydantic import BaseModel, Field


class FlightOrderRequestBody(BaseModel):
    """
    Request body for creating a flight order.
    The flight_offer should be pre-selected and price-confirmed before calling this endpoint.
    """

    flight_offer: dict = Field(
        ...,
        description="Pre-selected and price-confirmed flight offer from the search/pricing endpoints",
    )
    travelers: list[dict] = Field(
        ...,
        description="List of traveler information including contact details, documents, etc.",
    )
