import uuid
from json import dumps

import pytest
from amadeus.client.errors import ClientError

from backend.application.bookings.create_flight_order import (
    CreateFlightOrder,
    CreatedFlightBooking,
    FlightOrderProviderError,
    InvalidFlightOrderRequest,
)
from backend.infrastructure.flights.amadeus_flight_order_gateway import (
    AmadeusFlightOrderGateway,
)


USER_ID = uuid.uuid4()
BOOKING_ID = uuid.uuid4()


class StubFlightOrderProvider:
    def __init__(self, response=None):
        self.calls = []
        if response is None:
            response = {
                "id": "AMADEUS_ORDER_1",
                "associatedRecords": [{"reference": "PNR123"}],
                "flightOffers": [{"price": {"grandTotal": "120.50"}}],
            }
        self.response = response

    def create_order(self, order_request):
        self.calls.append(order_request)
        return self.response


class StubBookingRepository:
    def __init__(self):
        self.calls = []

    def create_booking(
        self,
        *,
        user_id,
        flight_order_id,
        order_response,
        total_price,
    ):
        self.calls.append(
            {
                "user_id": user_id,
                "flight_order_id": flight_order_id,
                "order_response": order_response,
                "total_price": total_price,
            }
        )
        return CreatedFlightBooking(
            id=BOOKING_ID,
            flight_order_id=flight_order_id,
            status="confirmed",
        )


class StubUserBookingCache:
    def __init__(self):
        self.invalidated_user_ids = []

    def invalidate_user_bookings(self, user_id):
        self.invalidated_user_ids.append(user_id)


class StubBookingEventPublisher:
    def __init__(self):
        self.created_events = []

    def publish_booking_created(self, *, booking_id, user_id, pnr, user_email):
        self.created_events.append(
            {
                "booking_id": booking_id,
                "user_id": user_id,
                "pnr": pnr,
                "user_email": user_email,
            }
        )


class StubAmadeusFlightService:
    def __init__(self):
        self.create_flight_order_calls = []

    def create_flight_order(self, order_request):
        self.create_flight_order_calls.append(order_request)
        return {"id": "AMADEUS_ORDER_1"}


class FailingAmadeusFlightService:
    def __init__(self, error):
        self.error = error
        self.create_flight_order_calls = []

    def create_flight_order(self, order_request):
        self.create_flight_order_calls.append(order_request)
        raise self.error


class FakeAmadeusResponse:
    def __init__(self, result):
        self.status_code = 400
        self.parsed = True
        self.result = result
        self.body = dumps(result)


def build_use_case(provider_response=None):
    provider = StubFlightOrderProvider(response=provider_response)
    repository = StubBookingRepository()
    cache = StubUserBookingCache()
    publisher = StubBookingEventPublisher()
    use_case = CreateFlightOrder(
        order_provider=provider,
        booking_repository=repository,
        booking_cache=cache,
        event_publisher=publisher,
    )
    return use_case, provider, repository, cache, publisher


def test_create_flight_order_persists_booking_invalidates_cache_and_publishes_event():
    use_case, provider, repository, cache, publisher = build_use_case()
    order_request = {
        "flight_offer": {"id": "offer_1"},
        "travelers": [{"id": "1"}],
    }

    booking = use_case.execute(
        user_id=USER_ID,
        user_email="traveler@example.com",
        order_request=order_request,
    )

    assert booking == CreatedFlightBooking(
        id=BOOKING_ID,
        flight_order_id="AMADEUS_ORDER_1",
        status="confirmed",
    )
    assert provider.calls == [order_request]
    assert provider.calls[0] is not order_request
    assert repository.calls == [
        {
            "user_id": USER_ID,
            "flight_order_id": "AMADEUS_ORDER_1",
            "order_response": provider.response,
            "total_price": 120.50,
        }
    ]
    assert cache.invalidated_user_ids == [USER_ID]
    assert publisher.created_events == [
        {
            "booking_id": BOOKING_ID,
            "user_id": USER_ID,
            "pnr": "PNR123",
            "user_email": "traveler@example.com",
        }
    ]


def test_create_flight_order_uses_zero_total_when_grand_total_is_invalid():
    use_case, _, repository, _, _ = build_use_case(
        provider_response={
            "id": "AMADEUS_ORDER_1",
            "associatedRecords": [{"reference": "PNR123"}],
            "flightOffers": [{"price": {"grandTotal": "invalid"}}],
        }
    )

    use_case.execute(
        user_id=USER_ID,
        user_email="traveler@example.com",
        order_request={"flight_offer": {}, "travelers": []},
    )

    assert repository.calls[0]["total_price"] == 0.0


def test_create_flight_order_rejects_provider_response_without_order_id():
    use_case, _, repository, cache, publisher = build_use_case(provider_response={})

    with pytest.raises(FlightOrderProviderError):
        use_case.execute(
            user_id=USER_ID,
            user_email="traveler@example.com",
            order_request={"flight_offer": {}, "travelers": []},
        )

    assert repository.calls == []
    assert cache.invalidated_user_ids == []
    assert publisher.created_events == []


def test_amadeus_flight_order_gateway_uses_create_flight_order_method():
    flight_service = StubAmadeusFlightService()
    gateway = AmadeusFlightOrderGateway(flight_service)
    order_request = {
        "flight_offer": {"id": "offer_1"},
        "travelers": [{"id": "1"}],
    }

    response = gateway.create_order(order_request)

    assert response == {"id": "AMADEUS_ORDER_1"}
    assert flight_service.create_flight_order_calls == [order_request]


def test_amadeus_flight_order_gateway_preserves_amadeus_client_error_detail():
    order_request = {
        "flight_offer": {"id": "offer_1"},
        "travelers": [{"id": "1"}],
    }
    amadeus_error = ClientError(
        FakeAmadeusResponse(
            {
                "errors": [
                    {
                        "code": 34651,
                        "title": "SEGMENT SELL FAILURE",
                        "detail": "Could not sell segment 1",
                    }
                ]
            }
        )
    )
    flight_service = FailingAmadeusFlightService(amadeus_error)
    gateway = AmadeusFlightOrderGateway(flight_service)

    with pytest.raises(InvalidFlightOrderRequest) as exc_info:
        gateway.create_order(order_request)

    assert str(exc_info.value) == (
        "Flight is no longer available for booking. Flight offers expire within minutes. "
        "Please search for flights again and complete the entire booking process quickly."
    )
    assert flight_service.create_flight_order_calls == [order_request]
