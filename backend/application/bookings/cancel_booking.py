from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from backend.models.bookings import BookingStatus


@dataclass(frozen=True)
class BookingCancellationRecord:
    id: UUID
    user_id: UUID
    flight_order_id: str | None
    status: str
    pnr: str | None


@dataclass(frozen=True)
class CancelBookingCommand:
    booking_id: UUID
    user_id: UUID
    user_email: str


@dataclass(frozen=True)
class CancelledBooking:
    id: UUID
    status: str
    message: str


class CancelBookingError(Exception):
    pass


class BookingNotFound(CancelBookingError):
    pass


class BookingAlreadyCancelled(CancelBookingError):
    pass


class BookingCannotBeCancelled(CancelBookingError):
    pass


class BookingCancellationRepository(Protocol):
    def get_user_booking_to_cancel(
        self, *, booking_id: UUID, user_id: UUID
    ) -> BookingCancellationRecord | None: ...

    def update_booking_status(self, booking_id: UUID, status: str) -> None: ...


class BookingCancellationProvider(Protocol):
    def cancel_order(self, flight_order_id: str) -> None: ...


class BookingCacheInvalidator(Protocol):
    def invalidate_user_bookings(self, user_id: UUID) -> None: ...


class BookingCancellationEventPublisher(Protocol):
    def publish_booking_cancelled(
        self,
        *,
        booking_id: UUID,
        user_id: UUID,
        pnr: str | None,
        user_email: str,
    ) -> None: ...


class CancelBooking:
    def __init__(
        self,
        *,
        booking_repository: BookingCancellationRepository,
        booking_cancellation_provider: BookingCancellationProvider,
        booking_cache: BookingCacheInvalidator,
        event_publisher: BookingCancellationEventPublisher,
    ):
        self.booking_repository = booking_repository
        self.booking_cancellation_provider = booking_cancellation_provider
        self.booking_cache = booking_cache
        self.event_publisher = event_publisher

    def execute(self, *, command: CancelBookingCommand) -> CancelledBooking:
        booking = self.booking_repository.get_user_booking_to_cancel(
            booking_id=command.booking_id,
            user_id=command.user_id,
        )
        if not booking:
            raise BookingNotFound

        if booking.status == BookingStatus.CANCELLED:
            raise BookingAlreadyCancelled

        if booking.status in (
            BookingStatus.REVERSED,
            BookingStatus.FAILED,
            BookingStatus.REFUNDED,
        ):
            raise BookingCannotBeCancelled

        if booking.flight_order_id:
            try:
                self.booking_cancellation_provider.cancel_order(booking.flight_order_id)
            except Exception:
                pass

        self.booking_repository.update_booking_status(
            booking.id, BookingStatus.CANCELLED
        )
        self.booking_cache.invalidate_user_bookings(command.user_id)
        self.event_publisher.publish_booking_cancelled(
            booking_id=booking.id,
            user_id=command.user_id,
            pnr=booking.pnr,
            user_email=command.user_email,
        )

        return CancelledBooking(
            id=booking.id,
            status=BookingStatus.CANCELLED,
            message="Booking has been successfully cancelled",
        )
