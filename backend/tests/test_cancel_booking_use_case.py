from uuid import uuid4

import pytest

from backend.application.bookings.cancel_booking import (
    BookingAlreadyCancelled,
    BookingCannotBeCancelled,
    BookingCancellationRecord,
    BookingNotFound,
    CancelBooking,
    CancelBookingCommand,
    CancelledBooking,
)
from backend.models.bookings import BookingStatus


BOOKING_ID = uuid4()
USER_ID = uuid4()


class StubBookingRepository:
    def __init__(self, booking: BookingCancellationRecord | None):
        self.booking = booking
        self.lookup_calls = []
        self.status_updates = []

    def get_user_booking_to_cancel(self, *, booking_id, user_id):
        self.lookup_calls.append({"booking_id": booking_id, "user_id": user_id})
        return self.booking

    def update_booking_status(self, booking_id, status: str) -> None:
        self.status_updates.append({"booking_id": booking_id, "status": status})


class StubBookingCancellationProvider:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.calls = []

    def cancel_order(self, flight_order_id: str) -> None:
        self.calls.append(flight_order_id)
        if self.should_fail:
            raise RuntimeError("Provider unavailable")


class StubBookingCache:
    def __init__(self):
        self.invalidated_user_ids = []

    def invalidate_user_bookings(self, user_id):
        self.invalidated_user_ids.append(user_id)


class StubBookingEventPublisher:
    def __init__(self):
        self.cancelled_events = []

    def publish_booking_cancelled(self, **kwargs) -> None:
        self.cancelled_events.append(kwargs)


def build_booking(
    *,
    status: str = BookingStatus.CONFIRMED,
    flight_order_id: str = "AMADEUS_ORDER_1",
    pnr: str | None = "PNR123",
):
    return BookingCancellationRecord(
        id=BOOKING_ID,
        user_id=USER_ID,
        flight_order_id=flight_order_id,
        status=status,
        pnr=pnr,
    )


def build_use_case(*, booking: BookingCancellationRecord | None, provider=None):
    repository = StubBookingRepository(booking=booking)
    if provider is None:
        provider = StubBookingCancellationProvider()
    cache = StubBookingCache()
    publisher = StubBookingEventPublisher()
    use_case = CancelBooking(
        booking_repository=repository,
        booking_cancellation_provider=provider,
        booking_cache=cache,
        event_publisher=publisher,
    )
    return use_case, repository, provider, cache, publisher


def build_command():
    return CancelBookingCommand(
        booking_id=BOOKING_ID,
        user_id=USER_ID,
        user_email="traveler@example.com",
    )


def test_cancel_booking_cancels_upstream_booking_and_publishes_event():
    booking = build_booking()
    use_case, repository, provider, cache, publisher = build_use_case(booking=booking)

    result = use_case.execute(command=build_command())

    assert result == CancelledBooking(
        id=BOOKING_ID,
        status=BookingStatus.CANCELLED,
        message="Booking has been successfully cancelled",
    )
    assert repository.lookup_calls == [
        {"booking_id": BOOKING_ID, "user_id": USER_ID},
    ]
    assert provider.calls == ["AMADEUS_ORDER_1"]
    assert repository.status_updates == [
        {"booking_id": BOOKING_ID, "status": BookingStatus.CANCELLED},
    ]
    assert cache.invalidated_user_ids == [USER_ID]
    assert publisher.cancelled_events == [
        {
            "booking_id": BOOKING_ID,
            "user_id": USER_ID,
            "pnr": "PNR123",
            "user_email": "traveler@example.com",
        }
    ]


def test_cancel_booking_continues_when_upstream_cancellation_fails():
    booking = build_booking()
    failing_provider = StubBookingCancellationProvider(should_fail=True)
    use_case, repository, _provider, cache, publisher = build_use_case(
        booking=booking,
        provider=failing_provider,
    )

    result = use_case.execute(command=build_command())

    assert result.status == BookingStatus.CANCELLED
    assert failing_provider.calls == ["AMADEUS_ORDER_1"]
    assert repository.status_updates == [
        {"booking_id": BOOKING_ID, "status": BookingStatus.CANCELLED},
    ]
    assert cache.invalidated_user_ids == [USER_ID]
    assert publisher.cancelled_events


def test_cancel_booking_rejects_missing_booking():
    use_case, repository, provider, cache, publisher = build_use_case(booking=None)

    with pytest.raises(BookingNotFound):
        use_case.execute(command=build_command())

    assert repository.lookup_calls == [
        {"booking_id": BOOKING_ID, "user_id": USER_ID},
    ]
    assert provider.calls == []
    assert cache.invalidated_user_ids == []
    assert publisher.cancelled_events == []


def test_cancel_booking_rejects_already_cancelled_booking():
    use_case, repository, provider, cache, publisher = build_use_case(
        booking=build_booking(status=BookingStatus.CANCELLED)
    )

    with pytest.raises(BookingAlreadyCancelled):
        use_case.execute(command=build_command())

    assert repository.status_updates == []
    assert provider.calls == []
    assert cache.invalidated_user_ids == []
    assert publisher.cancelled_events == []


def test_cancel_booking_rejects_non_cancellable_booking_status():
    use_case, repository, provider, cache, publisher = build_use_case(
        booking=build_booking(status=BookingStatus.FAILED)
    )

    with pytest.raises(BookingCannotBeCancelled):
        use_case.execute(command=build_command())

    assert repository.status_updates == []
    assert provider.calls == []
    assert cache.invalidated_user_ids == []
    assert publisher.cancelled_events == []
