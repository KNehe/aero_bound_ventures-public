import pytest
from unittest.mock import AsyncMock
from backend.models.bookings import Booking
from backend.crud.users import create_user
from backend.crud.bookings import create_booking
from backend.routers.flights import (
    get_confirm_flight_price_use_case,
    get_search_flights_use_case,
)


API_V1_PREFIX = "/api/v1"


class StubSearchFlightsUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, criteria):
        self.calls.append(criteria)
        return [{"id": "flight_1"}]


class StubConfirmFlightPriceUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, flight_offer):
        self.calls.append(flight_offer)
        return {"data": {"flightOffers": []}}


@pytest.fixture
def test_user(session):
    return create_user(session, "test_external@example.com", "password")


@pytest.fixture
def auth_header(client, test_user):
    # Overrides the authentication dependency to use the test user
    from backend.utils.security import get_current_user

    client.app.dependency_overrides[get_current_user] = lambda: test_user
    yield
    client.app.dependency_overrides.clear()


def test_initiate_payment_success(client, session, test_user, mocker, auth_header):
    booking = create_booking(
        session,
        Booking(
            user_id=test_user.id,
            flight_order_id="FLIGHT_123",
            total_price=100.0,
            status="pending",
        ),
    )

    mock_submit = mocker.patch(
        "backend.routers.payments.pesapal_client.submit_order_request",
        new_callable=AsyncMock,
    )
    mock_submit.return_value = {
        "order_tracking_id": "track_123",
        "merchant_reference": str(booking.id),
        "redirect_url": "https://pesapal.com/pay/123",
        "status": "200",
    }
    mocker.patch("backend.routers.payments.pesapal_client.ipn_id", "test_ipn_id")
    mocker.patch("backend.routers.payments.kafka_producer")

    payload = {
        "booking_id": str(booking.id),
        "amount": 100.0,
        "description": "Test payment",
        "callback_url": "https://frontend.com/callback",
        "billing_address": {
            "email_address": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        },
    }
    response = client.post("/payments/pesapal/initiate", json=payload)

    assert response.status_code == 200
    assert response.json()["redirect_url"] == "https://pesapal.com/pay/123"
    mock_submit.assert_called_once()


def test_search_flights_mock(client):
    use_case = StubSearchFlightsUseCase()
    client.app.dependency_overrides[get_search_flights_use_case] = lambda: use_case

    params = {
        "originLocationCode": "NYC",
        "destinationLocationCode": "LON",
        "departureDate": "2024-12-01",
        "adults": 1,
    }
    try:
        response = client.get(f"{API_V1_PREFIX}/shopping/flight-offers", params=params)
    finally:
        client.app.dependency_overrides.pop(get_search_flights_use_case, None)

    assert response.status_code == 200
    assert response.json() == [{"id": "flight_1"}]
    assert use_case.calls == [
        {
            "originLocationCode": "NYC",
            "destinationLocationCode": "LON",
            "departureDate": "2024-12-01",
            "adults": 1,
            "max": 5,
            "currencyCode": "USD",
        }
    ]


def test_confirm_price_route_uses_pricing_use_case(client):
    use_case = StubConfirmFlightPriceUseCase()
    client.app.dependency_overrides[get_confirm_flight_price_use_case] = (
        lambda: use_case
    )
    # Minimal flight offer payload matching FlightOffer schema
    payload = {
        "type": "flight-offer",
        "id": "1",
        "source": "GDS",
        "instantTicketingRequired": False,
        "nonHomogeneous": False,
        "oneWay": False,
        "isUpsellOffer": False,
        "lastTicketingDate": "2024-11-01",
        "numberOfBookableSeats": 1,
        "lastTicketingDateTime": "2024-11-01",
        "itineraries": [],
        "price": {
            "currency": "USD",
            "total": "100.0",
            "base": "90.0",
            "fees": [],
            "grandTotal": "100.0",
        },
        "pricingOptions": {"fareType": ["PUBLISHED"], "includedCheckedBagsOnly": False},
        "validatingAirlineCodes": ["AA"],
        "travelerPricings": [],
    }
    try:
        response = client.post(
            f"{API_V1_PREFIX}/shopping/flight-offers/pricing", json=payload
        )
    finally:
        client.app.dependency_overrides.pop(get_confirm_flight_price_use_case, None)

    assert response.status_code == 200
    assert response.json() == {
        "data": {"flightOffers": []},
        "result": None,
        "meta": None,
    }
    assert len(use_case.calls) == 1
    assert use_case.calls[0]["id"] == "1"
    assert use_case.calls[0]["price"] == {
        "currency": "USD",
        "total": "100.0",
        "base": "90.0",
        "fees": [],
        "grandTotal": "100.0",
        "billingCurrency": None,
        "taxes": None,
        "refundableTaxes": None,
    }
