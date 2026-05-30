import uuid
from unittest.mock import MagicMock

import pytest

from backend.application.bookings.get_seat_map import (
    InvalidSeatMapRequest,
    SeatMapBookingNotFound,
)
from backend.external_services.flight import AmadeusFlightService
from backend.main import app
from backend.models.users import UserInDB
from backend.routers.flights import get_seat_map_use_case
from backend.utils.security import get_current_user


API_V1_PREFIX = "/api/v1"


@pytest.fixture
def mock_user():
    return UserInDB(
        id=uuid.uuid4(),
        email="test@example.com",
        password="hashedpassword",
        is_active=True,
    )


@pytest.fixture
def authenticated_client(client, mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def seat_map_use_case():
    use_case = MagicMock()
    app.dependency_overrides[get_seat_map_use_case] = lambda: use_case
    yield use_case
    app.dependency_overrides.pop(get_seat_map_use_case, None)


@pytest.fixture
def flight_service():
    service = AmadeusFlightService()
    service.amadeus = MagicMock()
    return service


def test_view_seat_map_get_direct_id_success(
    authenticated_client, seat_map_use_case, mock_user
):
    seat_map_use_case.execute.return_value = [{"id": "seatmap_1"}]

    response = authenticated_client.get(
        f"{API_V1_PREFIX}/shopping/seatmaps?flightorderId=DIRECT_AMADEUS_ID_123"
    )

    assert response.status_code == 200
    assert response.json() == [{"id": "seatmap_1"}]
    seat_map_use_case.execute.assert_called_once_with(
        flight_order_reference="DIRECT_AMADEUS_ID_123",
        user_id=mock_user.id,
    )


def test_view_seat_map_get_db_uuid_success(
    authenticated_client, seat_map_use_case, mock_user
):
    booking_id = "550e8400-e29b-41d4-a716-446655440000"
    seat_map_use_case.execute.return_value = [{"id": "seatmap_db_1"}]

    response = authenticated_client.get(
        f"{API_V1_PREFIX}/shopping/seatmaps?flightorderId={booking_id}"
    )

    assert response.status_code == 200
    assert response.json() == [{"id": "seatmap_db_1"}]
    seat_map_use_case.execute.assert_called_once()
    assert (
        seat_map_use_case.execute.call_args.kwargs["flight_order_reference"]
        == booking_id
    )
    assert seat_map_use_case.execute.call_args.kwargs["user_id"] == mock_user.id


def test_view_seat_map_get_unauthorized_access(authenticated_client, seat_map_use_case):
    booking_id = "550e8400-e29b-41d4-a716-446655440000"
    seat_map_use_case.execute.side_effect = SeatMapBookingNotFound

    response = authenticated_client.get(
        f"{API_V1_PREFIX}/shopping/seatmaps?flightorderId={booking_id}"
    )

    assert response.status_code == 404
    assert "access denied" in response.json()["detail"].lower()


def test_view_seat_map_get_unauthenticated(client):
    response = client.get(f"{API_V1_PREFIX}/shopping/seatmaps?flightorderId=123")
    assert response.status_code == 401


def test_view_seat_map_get_invalid_provider_request(
    authenticated_client, seat_map_use_case
):
    seat_map_use_case.execute.side_effect = InvalidSeatMapRequest(
        "Seat map not available for this flight"
    )

    response = authenticated_client.get(
        f"{API_V1_PREFIX}/shopping/seatmaps?flightorderId=VALID_ID"
    )

    assert response.status_code == 400
    assert "Seat map not available" in response.json()["detail"]


def test_view_seat_map_post_success(authenticated_client, mocker, flight_service):
    mocker.patch("backend.routers.flights.amadeus_flight_service", flight_service)

    mock_response = MagicMock()
    mock_response.data = [{"id": "offer_seatmap_1"}]
    flight_service.amadeus.shopping.seatmaps.post.return_value = mock_response

    payload = {
        "type": "flight-offer",
        "id": "1",
        "source": "GDS",
        "instantTicketingRequired": False,
        "nonHomogeneous": False,
        "oneWay": False,
        "isUpsellOffer": False,
        "lastTicketingDate": "2025-01-01",
        "numberOfBookableSeats": 2,
        "lastTicketingDateTime": "2025-01-01T10:00:00",
        "itineraries": [],
        "price": {"currency": "USD", "total": "500.0", "base": "400.0", "fees": []},
        "pricingOptions": {"fareType": ["PUBLISHED"], "includedCheckedBagsOnly": False},
        "validatingAirlineCodes": ["DL"],
        "travelerPricings": [],
    }

    response = authenticated_client.post(
        f"{API_V1_PREFIX}/shopping/seatmaps", json=payload
    )

    assert response.status_code == 200
    assert response.json() == [{"id": "offer_seatmap_1"}]
    flight_service.amadeus.shopping.seatmaps.post.assert_called_once()
