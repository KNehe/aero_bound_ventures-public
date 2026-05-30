import uuid
from dataclasses import dataclass

import pytest

from backend.application.bookings.get_seat_map import (
    GetSeatMap,
    SeatMapBookingNotFound,
    SeatMapBookingRecord,
)
from backend.infrastructure.flights.amadeus_seat_map_gateway import (
    AmadeusSeatMapGateway,
)


@dataclass
class StubSeatMapRepository:
    booking: SeatMapBookingRecord | None
    calls: list[tuple[uuid.UUID, uuid.UUID]]

    def get_user_booking_for_seat_map(self, *, booking_id, user_id):
        self.calls.append((booking_id, user_id))
        return self.booking


@dataclass
class StubSeatMapProvider:
    responses: dict[str, list[dict]]
    calls: list[str]

    def view_seat_map(self, *, flight_order_id):
        self.calls.append(flight_order_id)
        return self.responses[flight_order_id]


@dataclass
class StubAmadeusFlightService:
    calls: list[str]

    def view_seat_map_get(self, flight_order_id):
        self.calls.append(flight_order_id)
        return [{"id": "seatmap_1"}]


def test_get_seat_map_uses_direct_reference_without_booking_lookup():
    repository = StubSeatMapRepository(booking=None, calls=[])
    provider = StubSeatMapProvider(
        responses={"DIRECT_AMADEUS_ID_123": [{"id": "seatmap_1"}]},
        calls=[],
    )

    use_case = GetSeatMap(
        booking_repository=repository,
        seat_map_provider=provider,
    )

    result = use_case.execute(
        flight_order_reference="DIRECT_AMADEUS_ID_123",
        user_id=uuid.uuid4(),
    )

    assert result == [{"id": "seatmap_1"}]
    assert repository.calls == []
    assert provider.calls == ["DIRECT_AMADEUS_ID_123"]


def test_get_seat_map_resolves_booking_uuid_to_order_reference():
    booking_id = uuid.uuid4()
    user_id = uuid.uuid4()
    repository = StubSeatMapRepository(
        booking=SeatMapBookingRecord(
            id=booking_id,
            user_id=user_id,
            flight_order_id="AMADEUS_ID_B123",
        ),
        calls=[],
    )
    provider = StubSeatMapProvider(
        responses={"AMADEUS_ID_B123": [{"id": "seatmap_db_1"}]},
        calls=[],
    )

    use_case = GetSeatMap(
        booking_repository=repository,
        seat_map_provider=provider,
    )

    result = use_case.execute(flight_order_reference=str(booking_id), user_id=user_id)

    assert result == [{"id": "seatmap_db_1"}]
    assert repository.calls == [(booking_id, user_id)]
    assert provider.calls == ["AMADEUS_ID_B123"]


def test_get_seat_map_raises_when_booking_is_missing():
    repository = StubSeatMapRepository(booking=None, calls=[])
    provider = StubSeatMapProvider(responses={}, calls=[])
    use_case = GetSeatMap(
        booking_repository=repository,
        seat_map_provider=provider,
    )

    with pytest.raises(SeatMapBookingNotFound):
        use_case.execute(
            flight_order_reference=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
        )


def test_amadeus_seat_map_gateway_uses_flight_order_lookup():
    flight_service = StubAmadeusFlightService(calls=[])
    gateway = AmadeusSeatMapGateway(flight_service)

    result = gateway.view_seat_map(flight_order_id="AMADEUS_ID_B123")

    assert result == [{"id": "seatmap_1"}]
    assert flight_service.calls == ["AMADEUS_ID_B123"]
