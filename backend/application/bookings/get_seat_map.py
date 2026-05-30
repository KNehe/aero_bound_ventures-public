from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True)
class SeatMapBookingRecord:
    id: UUID
    user_id: UUID
    flight_order_id: str


class SeatMapError(Exception):
    pass


class SeatMapBookingNotFound(SeatMapError):
    pass


class InvalidSeatMapRequest(SeatMapError):
    pass


class SeatMapProviderError(SeatMapError):
    pass


class SeatMapBookingRepository(Protocol):
    def get_user_booking_for_seat_map(
        self, *, booking_id: UUID, user_id: UUID
    ) -> SeatMapBookingRecord | None: ...


class SeatMapProvider(Protocol):
    def view_seat_map(self, *, flight_order_id: str) -> list[dict[str, Any]]: ...


class GetSeatMap:
    def __init__(
        self,
        *,
        booking_repository: SeatMapBookingRepository,
        seat_map_provider: SeatMapProvider,
    ):
        self.booking_repository = booking_repository
        self.seat_map_provider = seat_map_provider

    def execute(
        self, *, flight_order_reference: str, user_id: UUID
    ) -> list[dict[str, Any]]:
        try:
            booking_id = UUID(flight_order_reference)
        except ValueError:
            return self.seat_map_provider.view_seat_map(
                flight_order_id=flight_order_reference
            )

        booking = self.booking_repository.get_user_booking_for_seat_map(
            booking_id=booking_id,
            user_id=user_id,
        )
        if not booking:
            raise SeatMapBookingNotFound

        return self.seat_map_provider.view_seat_map(
            flight_order_id=booking.flight_order_id
        )
