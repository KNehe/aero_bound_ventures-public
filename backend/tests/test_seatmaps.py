import pytest
import uuid
from unittest.mock import MagicMock
from amadeus.client.errors import ClientError
from backend.main import app
from backend.external_services.flight import AmadeusFlightService
from backend.models.bookings import Booking
from backend.models.users import UserInDB
from backend.utils.security import get_current_user


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
def flight_service():
    service = AmadeusFlightService()
    service.amadeus = MagicMock()
    return service


def test_view_seat_map_get_direct_id_success(
    authenticated_client, mocker, flight_service
):
    # Patch the service used in the router
    mocker.patch("backend.routers.flights.amadeus_flight_service", flight_service)

    # Mock Amadeus response
    mock_response = MagicMock()
    mock_response.data = [{"id": "seatmap_1"}]
    flight_service.amadeus.shopping.seatmaps.get.return_value = mock_response

    # Call with a direct Amadeus ID (not a UUID)
    response = authenticated_client.get(
        "/shopping/seatmaps?flightorderId=DIRECT_AMADEUS_ID_123"
    )

    assert response.status_code == 200
    assert response.json() == [{"id": "seatmap_1"}]
    flight_service.amadeus.shopping.seatmaps.get.assert_called_once_with(
        flightOrderId="DIRECT_AMADEUS_ID_123"
    )


def test_view_seat_map_get_db_uuid_success(
    authenticated_client, session, mocker, flight_service, mock_user
):
    mocker.patch("backend.routers.flights.amadeus_flight_service", flight_service)

    # Ensure user exists in DB
    session.add(mock_user)
    session.commit()

    # Create a booking in the test DB for the mock user
    booking = Booking(
        user_id=mock_user.id,
        flight_order_id="AMADEUS_ID_B123",
        total_price=150.0,
        currency="USD",
        status="confirmed",
        amadeus_order_response={},
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)

    # Mock Amadeus response
    mock_response = MagicMock()
    mock_response.data = [{"id": "seatmap_db_1"}]
    flight_service.amadeus.shopping.seatmaps.get.return_value = mock_response

    # Call with the database UUID
    response = authenticated_client.get(
        f"/shopping/seatmaps?flightorderId={booking.id}"
    )

    assert response.status_code == 200
    assert response.json() == [{"id": "seatmap_db_1"}]
    # Verify it called Amadeus with the mapped ID
    flight_service.amadeus.shopping.seatmaps.get.assert_called_once_with(
        flightOrderId="AMADEUS_ID_B123"
    )


def test_view_seat_map_get_unauthorized_access(
    authenticated_client, session, mocker, flight_service
):
    mocker.patch("backend.routers.flights.amadeus_flight_service", flight_service)

    # Create ANOTHER user in DB
    other_user = UserInDB(
        id=uuid.uuid4(), email="other@example.com", password="hashedpassword"
    )
    session.add(other_user)
    session.commit()

    # Create a booking for ANOTHER user
    booking = Booking(
        user_id=other_user.id,
        flight_order_id="OTHER_USER_ORDER",
        total_price=200.0,
        currency="USD",
        status="confirmed",
        amadeus_order_response={},
    )
    session.add(booking)
    session.commit()

    # Attempt to access someone else's booking via UUID
    response = authenticated_client.get(
        f"/shopping/seatmaps?flightorderId={booking.id}"
    )

    assert response.status_code == 404
    assert "access denied" in response.json()["detail"].lower()


def test_view_seat_map_get_unauthenticated(client):
    # Call without auth override
    response = client.get("/shopping/seatmaps?flightorderId=123")
    assert response.status_code == 401


def test_view_seat_map_get_amadeus_api_error(
    authenticated_client, mocker, flight_service
):
    mocker.patch("backend.routers.flights.amadeus_flight_service", flight_service)

    # Mock Amadeus ClientError
    mock_error_response = MagicMock()
    mock_error_response.body = (
        '{"errors": [{"detail": "Seat map not available for this flight"}]}'
    )
    error = ClientError(mock_error_response)

    flight_service.amadeus.shopping.seatmaps.get.side_effect = error

    response = authenticated_client.get("/shopping/seatmaps?flightorderId=VALID_ID")

    assert response.status_code == 400
    assert "Seat map not available" in response.json()["detail"]


def test_view_seat_map_post_success(authenticated_client, mocker, flight_service):
    mocker.patch("backend.routers.flights.amadeus_flight_service", flight_service)

    mock_response = MagicMock()
    mock_response.data = [{"id": "offer_seatmap_1"}]
    flight_service.amadeus.shopping.seatmaps.post.return_value = mock_response

    # Minimal flight offer payload
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

    response = authenticated_client.post("/shopping/seatmaps", json=payload)

    assert response.status_code == 200
    assert response.json() == [{"id": "offer_seatmap_1"}]
    flight_service.amadeus.shopping.seatmaps.post.assert_called_once()
