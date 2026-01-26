from typing import List, Optional
from pydantic import BaseModel, Field


class DepartureArrival(BaseModel):
    """
    Represents the departure or arrival details of a flight segment.
    """

    iataCode: str
    at: str
    terminal: Optional[str] = None


class Aircraft(BaseModel):
    """
    Represents the aircraft details.
    """

    code: str


class Operating(BaseModel):
    """
    Represents the operating carrier of the flight.
    """

    carrierCode: str


class Segment(BaseModel):
    """
    Represents a single segment of a flight itinerary.
    """

    departure: DepartureArrival
    arrival: DepartureArrival
    carrierCode: str
    number: str
    aircraft: Aircraft
    operating: Operating
    duration: Optional[str] = None
    id: Optional[str] = None
    numberOfStops: Optional[int] = None
    blacklistedInEU: Optional[bool] = None
    co2Emissions: Optional[list] = None


class Itinerary(BaseModel):
    """
    Represents an itinerary, which is a collection of flight segments.
    """

    segments: list
    duration: Optional[str] = None


class Fee(BaseModel):
    """
    Represents a fee associated with the flight price.
    """

    amount: str
    type: str


class Price(BaseModel):
    """
    Represents the price details for a flight offer or traveler.
    """

    currency: str
    total: str
    base: str
    fees: list = None
    grandTotal: str = None
    billingCurrency: str = None
    taxes: list = None
    refundableTaxes: str = None


class PricingOptions(BaseModel):
    """
    Represents the pricing options for the flight offer.
    """

    fareType: list
    includedCheckedBagsOnly: bool


class IncludedBags(BaseModel):
    """
    Represents included baggage information.
    """

    quantity: int


class AdditionalServices(BaseModel):
    """
    Represents additional services like chargeable seats.
    """

    chargeableSeatNumber: Optional[str] = None


class FareDetailsBySegment(BaseModel):
    """
    Represents fare details for a specific flight segment.
    """

    segmentId: str
    cabin: str
    fareBasis: str
    Class: str = Field(alias="class")
    brandedFare: Optional[str] = None
    includedCheckedBags: Optional[IncludedBags] = None
    includedCabinBags: Optional[IncludedBags] = None
    additionalServices: Optional[AdditionalServices] = None


class TravelerPricing(BaseModel):
    """
    Represents the pricing for a single traveler.
    """

    travelerId: str
    fareOption: str
    travelerType: str
    price: Price
    fareDetailsBySegment: list
    associatedAdultId: str = None


class FlightOffer(BaseModel):
    """
    The main model representing the full flight offer.
    """

    type: str
    id: str
    source: str
    itineraries: List[Itinerary]
    price: Price
    pricingOptions: PricingOptions
    validatingAirlineCodes: list
    travelerPricings: list
    instantTicketingRequired: Optional[bool] = None
    nonHomogeneous: Optional[bool] = None
    oneWay: Optional[bool] = None
    isUpsellOffer: Optional[bool] = None
    lastTicketingDate: Optional[str] = None
    lastTicketingDateTime: Optional[str] = None
    numberOfBookableSeats: Optional[int] = None
    totalPrice: Optional[str] = None
    totalPriceBase: Optional[str] = None
    fareType: Optional[str] = None
    paymentCardRequired: Optional[bool] = None
