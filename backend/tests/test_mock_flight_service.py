"""
Tests for the MockFlightService implementation.

Validates that mock responses match the expected shape for all flight operations,
ensuring frontend compatibility when running in mock mode.
"""

import pytest
from backend.external_services.mock_flight_service import MockFlightService


@pytest.fixture
def mock_service():
    return MockFlightService()


class TestMockFlightSearch:
    def test_search_flights_returns_mock_response(self, mock_service):
        result = mock_service.search_flights({})
        assert hasattr(result, "data")
        assert isinstance(result.data, list)
        assert len(result.data) > 0

    def test_search_flights_get_returns_list(self, mock_service):
        result = mock_service.search_flights_get({})
        assert isinstance(result, list)
        assert len(result) > 0

    def test_flight_offer_has_required_fields(self, mock_service):
        result = mock_service.search_flights_get({})
        offer = result[0]
        assert "type" in offer
        assert "id" in offer
        assert "itineraries" in offer
        assert "price" in offer
        assert "travelerPricings" in offer
        assert "validatingAirlineCodes" in offer

    def test_flight_offer_itinerary_structure(self, mock_service):
        result = mock_service.search_flights_get({})
        offer = result[0]
        itinerary = offer["itineraries"][0]
        assert "duration" in itinerary
        assert "segments" in itinerary
        segment = itinerary["segments"][0]
        assert "departure" in segment
        assert "arrival" in segment
        assert "carrierCode" in segment
        assert "iataCode" in segment["departure"]
        assert "iataCode" in segment["arrival"]

    def test_flight_offer_price_structure(self, mock_service):
        result = mock_service.search_flights_get({})
        price = result[0]["price"]
        assert "currency" in price
        assert "total" in price
        assert "grandTotal" in price
        assert price["currency"] == "USD"

    def test_search_filters_by_origin_destination(self, mock_service):
        result = mock_service.search_flights_get(
            {"originLocationCode": "NBO", "destinationLocationCode": "LHR"}
        )
        assert isinstance(result, list)
        assert len(result) > 0

    def test_search_unmatched_filter_returns_all(self, mock_service):
        """When filters match nothing, all results are returned for better demo experience."""
        all_results = mock_service.search_flights_get({})
        filtered = mock_service.search_flights_get(
            {"originLocationCode": "XXX", "destinationLocationCode": "YYY"}
        )
        assert len(filtered) == len(all_results)


class TestMockFlightPricing:
    def test_confirm_price_returns_mock_response(self, mock_service):
        result = mock_service.confirm_price({})
        assert hasattr(result, "data")
        assert isinstance(result.data, dict)

    def test_pricing_has_flight_offers(self, mock_service):
        result = mock_service.confirm_price({})
        assert "flightOffers" in result.data
        assert isinstance(result.data["flightOffers"], list)
        assert len(result.data["flightOffers"]) > 0


class TestMockFlightOrder:
    def test_create_flight_order(self, mock_service):
        result = mock_service.create_flight_order({"travelers": []})
        assert "id" in result
        assert result["id"].startswith("MOCK_")
        assert "associatedRecords" in result
        assert "flightOffers" in result
        assert "travelers" in result

    def test_order_has_pnr(self, mock_service):
        """PNR is critical for the admin panel (AmadeusOrderResponse.associatedRecords)."""
        result = mock_service.create_flight_order({})
        associated = result["associatedRecords"]
        assert len(associated) > 0
        assert "reference" in associated[0]
        assert associated[0]["reference"].startswith("MK")

    def test_order_has_flight_offers_with_price(self, mock_service):
        """Frontend extracts price from flightOffers[0].price.grandTotal."""
        result = mock_service.create_flight_order({})
        offers = result["flightOffers"]
        assert len(offers) > 0
        assert "price" in offers[0]
        assert "grandTotal" in offers[0]["price"]

    def test_created_order_retrievable(self, mock_service):
        order = mock_service.create_flight_order({})
        order_id = order["id"]
        retrieved = mock_service.get_flight_order(order_id)
        assert retrieved["id"] == order_id

    def test_get_unknown_order_returns_fixture(self, mock_service):
        result = mock_service.get_flight_order("NONEXISTENT_123")
        assert "id" in result
        assert "flightOffers" in result

    def test_get_multiple_orders(self, mock_service):
        result = mock_service.get_flight_orders(["ORDER_1", "ORDER_2"])
        assert isinstance(result, list)
        assert len(result) == 2


class TestMockCancellation:
    def test_cancel_flight_order(self, mock_service):
        result = mock_service.cancel_flight_order("ORDER_123")
        assert hasattr(result, "status_code")
        assert result.status_code == 204

    def test_cancel_removes_from_store(self, mock_service):
        order = mock_service.create_flight_order({})
        order_id = order["id"]
        mock_service.cancel_flight_order(order_id)
        # After cancellation, retrieving should return the default fixture
        retrieved = mock_service.get_flight_order(order_id)
        assert retrieved["id"] != order_id


class TestMockSeatMap:
    def test_seat_map_get(self, mock_service):
        result = mock_service.view_seat_map_get("ORDER_123")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_seat_map_post(self, mock_service):
        result = mock_service.view_seat_map_post({"id": "1"})
        assert isinstance(result, list)
        assert len(result) > 0

    def test_seat_map_has_deck_structure(self, mock_service):
        result = mock_service.view_seat_map_get("ORDER_123")
        seatmap = result[0]
        assert "decks" in seatmap
        deck = seatmap["decks"][0]
        assert "seats" in deck
        assert "deckConfiguration" in deck

    def test_seat_has_availability_and_pricing(self, mock_service):
        result = mock_service.view_seat_map_get("ORDER_123")
        seats = result[0]["decks"][0]["seats"]
        seat = seats[0]
        assert "number" in seat
        assert "travelerPricing" in seat
        pricing = seat["travelerPricing"][0]
        assert "seatAvailabilityStatus" in pricing
        assert "price" in pricing


class TestMockAirportSearch:
    def test_airport_search_returns_list(self, mock_service):
        result = mock_service.airport_city_search({"keyword": "nairobi"})
        assert isinstance(result, list)
        assert len(result) > 0

    def test_airport_search_filters_by_keyword(self, mock_service):
        result = mock_service.airport_city_search({"keyword": "NBO"})
        assert all(
            "NBO" in loc.get("iataCode", "")
            or "NBO" in loc.get("address", {}).get("cityCode", "")
            for loc in result
        )

    def test_airport_has_required_fields(self, mock_service):
        result = mock_service.airport_city_search({})
        loc = result[0]
        assert "name" in loc
        assert "iataCode" in loc
        assert "address" in loc
        assert "subType" in loc


class TestMockDestinations:
    def test_destinations_returns_list(self, mock_service):
        result = mock_service.get_most_travelled_destinations("NBO", "2026-01")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_destination_has_analytics(self, mock_service):
        result = mock_service.get_most_travelled_destinations("NBO", "2026-01")
        dest = result[0]
        assert "destination" in dest
        assert "analytics" in dest


class TestMockAccessToken:
    def test_access_token_returns_string(self, mock_service):
        token = mock_service.get_amadeus_access_token()
        assert isinstance(token, str)
        assert len(token) > 0
