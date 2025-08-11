from pydantic import BaseModel, Field
import enum
from typing import Any


class TravelerType(str, enum.Enum):
    ADULT = "ADULT"
    CHILD = "CHILD"
    HELD_INFANT = "HELD_INFANT"


class CabinType(str, enum.Enum):
    ECONOMY = "ECONOMY"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"


# REQUEST MODELS
# Define the nested Pydantic models first
class DepartureDateTimeRange(BaseModel):
    """
    Model for the departure date and time range.
    """

    date: str
    time: str = "00:00:00"


class OriginDestination(BaseModel):
    """
    Model for a single leg of the journey.
    """

    id: str
    originLocationCode: str
    destinationLocationCode: str
    departureDateTimeRange: DepartureDateTimeRange


class Traveler(BaseModel):
    """
    Model for a single traveler.
    """

    id: str
    travelerType: TravelerType
    associatedAdultId: str | None = None  # This is optional for ADULTs


class AdditionalInformation(BaseModel):
    """
    Model for additional search information.
    """

    chargeableCheckedBags: bool
    brandedFares: bool
    fareRules: bool


class PricingOptions(BaseModel):
    """
    Model for pricing-related search criteria.
    """

    includedCheckedBagsOnly: bool


class CarrierRestrictions(BaseModel):
    blacklistedInEUAllowed: bool
    includedCarrierCodes: list[str]


class CabinRestriction(BaseModel):
    cabin: CabinType
    coverage: str = "MOST_SEGMENTS"
    originDestinationIds: list[str]


class ConnectionRestriction(BaseModel):
    airportChangeAllowed: bool
    technicalStopsAllowed: bool


class FlightFilters(BaseModel):
    crossBorderAllowed: bool
    moreOvernightsAllowed: bool
    returnToDepartureAirport: bool
    railSegmentAllowed: bool
    busSegmentAllowed: bool
    carrierRestrictions: CarrierRestrictions
    cabinRestrictions: list[CabinRestriction]
    connectionRestriction: ConnectionRestriction


class SearchCriteria(BaseModel):
    excludeAllotments: bool
    addOneWayOffers: bool
    maxFlightOffers: int
    allowAlternativeFareOptions: bool
    oneFlightOfferPerDay: bool
    additionalInformation: AdditionalInformation
    pricingOptions: PricingOptions
    flightFilters: FlightFilters


# The main request body model
class AmadeusFlightSearchRequest(BaseModel):
    currencyCode: str = Field(min_length=3, max_length=3)
    originDestinations: list[OriginDestination]
    travelers: list[Traveler]
    sources: list[str]
    searchCriteria: SearchCriteria


# Nested Models
class Itinerary(BaseModel):
    duration: str
    segments: list["Segment"]


class Segment(BaseModel):
    departure: "Location"
    arrival: "Location"
    carrierCode: str
    number: str
    aircraft: "Aircraft"
    operating: "Operating"
    duration: str
    id: str
    numberOfStops: int
    blacklistedInEU: bool


class Location(BaseModel):
    iataCode: str
    terminal: str
    at: str


class Aircraft(BaseModel):
    code: str


class Operating(BaseModel):
    carrierCode: str


class Price(BaseModel):
    currency: str
    total: str
    base: str
    fees: list["Fee"]
    grandTotal: str
    additionalServices: list["AdditionalService"]


class Fee(BaseModel):
    amount: str
    type: str


class AdditionalService(BaseModel):
    amount: str
    type: str


class PricingOptions(BaseModel):
    fareType: list[str]
    includedCheckedBagsOnly: bool


class TravelerPricing(BaseModel):
    travelerId: str
    fareOption: str
    travelerType: str
    price: "TravelerPrice"
    fareDetailsBySegment: list["FareDetailsBySegment"]


class TravelerPrice(BaseModel):
    currency: str
    total: str
    base: str


class FareDetailsBySegment(BaseModel):
    segmentId: str
    cabin: str
    fareBasis: str
    brandedFare: str
    brandedFareLabel: str
    class_: str = Field(
        ..., alias="class"
    )  # Using Field and alias to handle 'class' keyword
    includedCheckedBags: "Bags"
    includedCabinBags: "Bags"
    amenities: list["Amenity"]


class Bags(BaseModel):
    quantity: int


class Amenity(BaseModel):
    description: str
    isChargeable: bool
    amenityType: str
    amenityProvider: "AmenityProvider"


class AmenityProvider(BaseModel):
    name: str


# Root Model
class FlightOfferRequest(BaseModel):
    type: str = "flight-offer"
    id: str
    source: str
    instantTicketingRequired: bool
    nonHomogeneous: bool
    oneWay: bool
    isUpsellOffer: bool
    lastTicketingDate: str
    lastTicketingDateTime: str
    numberOfBookableSeats: int
    itineraries: list[Itinerary]
    price: Price
    pricingOptions: PricingOptions
    validatingAirlineCodes: list[str]
    travelerPricings: list[TravelerPricing]


# RESPONSE MODELS
class FlightOffer(BaseModel):
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
    itineraries: list[dict[str, Any]]
    price: dict[str, Any]
    pricingOptions: dict[str, Any]
    validatingAirlineCodes: list[str]
    travelerPricings: list[dict[str, Any]]

    # Optional fields that may not always be present
    totalPrice: str | None = None
    totalPriceBase: str | None = None
    fareType: str | None = None


class FlightSearchResponse(BaseModel):
    data: list[FlightOffer]
    dictionaries: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None


class FlightPricingResponse(BaseModel):
    data: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None
