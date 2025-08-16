from pydantic import BaseModel, Field


class DepartureDateTimeRange(BaseModel):
    date: str
    time: str


class OriginDestination(BaseModel):
    id: str
    originLocationCode: str
    destinationLocationCode: str
    departureDateTimeRange: DepartureDateTimeRange


class Traveler(BaseModel):
    id: str
    travelerType: str
    associatedAdultId: str | None = None


class AdditionalInformation(BaseModel):
    chargeableCheckedBags: bool
    brandedFares: bool
    fareRules: bool


class PricingOptions(BaseModel):
    includedCheckedBagsOnly: bool


class CarrierRestrictions(BaseModel):
    blacklistedInEUAllowed: bool
    includedCarrierCodes: list[str]


class CabinRestriction(BaseModel):
    cabin: str
    coverage: str
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


class FlightSearchRequestPost(BaseModel):
    currencyCode: str
    originDestinations: list[OriginDestination]
    travelers: list[Traveler]
    sources: list[str]
    searchCriteria: SearchCriteria


class FlightSearchRequestGet(BaseModel):
    originLocationCode: str
    destinationLocationCode: str
    departureDate: str
    adults: int = Field(default=1)
    max: int = Field(default=5)
    returnDate: str | None = None
    children: int | None = None
    infants: int | None = None
    travelClass: str | None = None
    includedAirlineCodes: str | None = None
    excludedAirlineCodes: str | None = None
    nonStop: bool | None = None
    currencyCode: str = Field(default="USD")
    maxPrice: int | None = None
