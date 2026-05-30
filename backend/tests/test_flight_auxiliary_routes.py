from backend.routers.flights import (
    get_location_search_use_case,
    get_travelled_destinations_use_case,
)


API_V1_PREFIX = "/api/v1"


class StubLocationSearchUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, criteria):
        self.calls.append(criteria)
        return [
            {
                "type": "location",
                "subType": "AIRPORT",
                "name": "Jomo Kenyatta International",
                "detailedName": "Jomo Kenyatta International Airport",
                "id": "ANBO",
                "self": {
                    "href": "https://example.com/locations/ANBO",
                    "methods": ["GET"],
                },
                "timeZoneOffset": "+03:00",
                "iataCode": "NBO",
                "geoCode": {"latitude": -1.3192, "longitude": 36.9278},
                "address": {
                    "cityName": "Nairobi",
                    "cityCode": "NBO",
                    "countryName": "Kenya",
                    "countryCode": "KE",
                    "regionCode": "AFR",
                },
                "analytics": None,
            }
        ]


class StubTravelledDestinationsUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, *, origin_city_code, period):
        self.calls.append(
            {
                "origin_city_code": origin_city_code,
                "period": period,
            }
        )
        return [{"destination": "MBA", "analytics": {"flights": {"score": 42}}}]


def test_post_flight_offers_route_is_removed(client):
    response = client.post(f"{API_V1_PREFIX}/shopping/flight-offers", json={})

    assert response.status_code == 405


def test_location_search_route_uses_location_search_use_case(client):
    use_case = StubLocationSearchUseCase()
    client.app.dependency_overrides[get_location_search_use_case] = lambda: use_case

    try:
        response = client.get(
            f"{API_V1_PREFIX}/reference-data/locations",
            params={"keyword": "NBO", "sub_type": "AIRPORT"},
        )
    finally:
        client.app.dependency_overrides.pop(get_location_search_use_case, None)

    assert response.status_code == 200
    assert response.json()[0]["iataCode"] == "NBO"
    assert use_case.calls == [{"keyword": "NBO", "sub_type": "AIRPORT"}]


def test_travelled_destinations_route_uses_use_case(client):
    use_case = StubTravelledDestinationsUseCase()
    client.app.dependency_overrides[get_travelled_destinations_use_case] = (
        lambda: use_case
    )

    try:
        response = client.get(
            f"{API_V1_PREFIX}/analytics/most-travelled-destinations",
            params={"origin_city_code": "NBO", "period": "2026-01"},
        )
    finally:
        client.app.dependency_overrides.pop(get_travelled_destinations_use_case, None)

    assert response.status_code == 200
    assert response.json() == [
        {"destination": "MBA", "analytics": {"flights": {"score": 42}}}
    ]
    assert use_case.calls == [
        {
            "origin_city_code": "NBO",
            "period": "2026-01",
        }
    ]
