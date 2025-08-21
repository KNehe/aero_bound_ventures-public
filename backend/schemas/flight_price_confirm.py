from pydantic import BaseModel, Field


class DepartureArrival(BaseModel):
    """
    Represents the departure or arrival details of a flight segment.
    """

    iataCode: str
    at: str


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
    duration: str
    id: str
    numberOfStops: int
    blacklistedInEU: bool


class Itinerary(BaseModel):
    """
    Represents an itinerary, which is a collection of flight segments.
    """

    duration: str
    segments: list


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


class FareDetailsBySegment(BaseModel):
    """
    Represents fare details for a specific flight segment.
    """

    segmentId: str
    cabin: str
    fareBasis: str
    Class: str = Field(alias="class")
    includedCheckedBags: IncludedBags = None
    includedCabinBags: IncludedBags = None


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
    instantTicketingRequired: bool
    nonHomogeneous: bool
    oneWay: bool
    isUpsellOffer: bool
    lastTicketingDate: str
    lastTicketingDateTime: str
    numberOfBookableSeats: int
    itineraries: list
    price: Price
    pricingOptions: PricingOptions
    validatingAirlineCodes: list
    travelerPricings: list
    totalPrice: str = None
    totalPriceBase: str = None
    fareType: str = None
