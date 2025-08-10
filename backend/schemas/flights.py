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
