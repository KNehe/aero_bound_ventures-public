from pydantic import BaseModel, Field
from amadeus import Location


class AirportCitySearchRequest(BaseModel):
    keyword: str
    sub_type: str = Field(default=Location.ANY)


class Self(BaseModel):
    href: str
    methods: list[str]


class GeoCode(BaseModel):
    latitude: float
    longitude: float


class Address(BaseModel):
    cityName: str
    cityCode: str
    countryName: str
    countryCode: str
    regionCode: str


class Travelers(BaseModel):
    score: int


# This can be optional
class Analytics(BaseModel):
    travelers: Travelers


class AirportCitySearchResponse(BaseModel):
    type: str
    subType: str
    name: str
    detailedName: str
    id: str
    self: Self = Field(alias="self")
    timeZoneOffset: str
    iataCode: str
    geoCode: GeoCode
    address: Address
    analytics: Analytics | None = None
