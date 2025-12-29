import pytest
from unittest.mock import AsyncMock
from backend.models.bookings import Booking
from backend.crud.users import create_user
from backend.crud.bookings import create_booking


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


def test_search_flights_mock(client, mocker):
    mock_search = mocker.patch(
        "backend.routers.flights.amadeus_flight_service.search_flights_get"
    )
    mock_search.return_value = [{"id": "flight_1"}]

    params = {
        "originLocationCode": "NYC",
        "destinationLocationCode": "LON",
        "departureDate": "2024-12-01",
        "adults": 1,
    }
    response = client.get("/shopping/flight-offers", params=params)

    assert response.status_code == 200
    mock_search.assert_called_once()


def test_confirm_price_mock(client, mocker):
    mock_price = mocker.patch(
        "backend.routers.flights.amadeus_flight_service.confirm_price"
    )
    mock_price.return_value = {"data": {"flightOffers": []}}

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
    response = client.post("/shopping/flight-offers/pricing", json=payload)

    assert response.status_code == 200
    mock_price.assert_called_once()
