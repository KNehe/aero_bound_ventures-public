from uuid import uuid4

import pytest

from backend.application.payments.process_payment_notification import (
    PaymentNotificationBookingRecord,
    ProcessPaymentNotification,
    ProcessPaymentNotificationCommand,
)
from backend.models.bookings import BookingStatus


DEFAULT_BOOKING = object()


class StubPaymentNotificationBookingRepository:
    def __init__(self, booking: PaymentNotificationBookingRecord | None):
        self.booking = booking
        self.lookup_calls = []
        self.status_updates = []

    def get_payment_notification_booking(
        self, booking_id: str
    ) -> PaymentNotificationBookingRecord | None:
        self.lookup_calls.append(booking_id)
        return self.booking

    def update_payment_booking_status(self, booking_id, status: str) -> None:
        self.status_updates.append({"booking_id": booking_id, "status": status})


class StubPaymentStatusProvider:
    def __init__(self, payment_status=None, error: Exception | None = None):
        self.payment_status = payment_status or {}
        self.error = error
        self.calls = []

    async def get_payment_status(self, payment_order_id: str):
        self.calls.append(payment_order_id)
        if self.error:
            raise self.error
        return self.payment_status


class StubPaymentEventPublisher:
    def __init__(self):
        self.successful = []

    def publish_payment_successful(self, **kwargs) -> None:
        self.successful.append(kwargs)


def build_booking() -> PaymentNotificationBookingRecord:
    return PaymentNotificationBookingRecord(
        id=uuid4(),
        user_id=uuid4(),
        user_email="traveler@example.com",
        pnr="ABC123",
    )


def build_use_case(
    *,
    booking=DEFAULT_BOOKING,
    payment_status=None,
    error: Exception | None = None,
):
    repository = StubPaymentNotificationBookingRepository(
        build_booking() if booking is DEFAULT_BOOKING else booking
    )
    provider = StubPaymentStatusProvider(payment_status, error)
    publisher = StubPaymentEventPublisher()
    use_case = ProcessPaymentNotification(
        booking_repository=repository,
        payment_status_provider=provider,
        event_publisher=publisher,
    )
    return use_case, repository, provider, publisher


def build_command(reference: str | None = "booking-id-1234567890"):
    return ProcessPaymentNotificationCommand(
        payment_order_id="track_123",
        merchant_reference=reference,
        notification_type="IPNCHANGE",
    )


@pytest.mark.asyncio
async def test_process_payment_notification_marks_success_and_publishes_event():
    booking = build_booking()
    use_case, repository, provider, publisher = build_use_case(
        booking=booking,
        payment_status={"status_code": 1},
    )

    result = await use_case.execute(build_command())

    assert result.as_response() == {
        "orderNotificationType": "IPNCHANGE",
        "orderTrackingId": "track_123",
        "orderMerchantReference": "booking-id-1234567890",
        "status": 200,
    }
    assert repository.lookup_calls == ["booking-id"]
    assert provider.calls == ["track_123"]
    assert repository.status_updates == [
        {"booking_id": booking.id, "status": BookingStatus.PAID}
    ]
    assert publisher.successful == [
        {
            "booking_id": booking.id,
            "user_id": booking.user_id,
            "user_email": booking.user_email,
            "pnr": booking.pnr,
        }
    ]


@pytest.mark.asyncio
async def test_process_payment_notification_marks_failed_without_event():
    booking = build_booking()
    use_case, repository, _provider, publisher = build_use_case(
        booking=booking,
        payment_status={"status_code": 2},
    )

    result = await use_case.execute(build_command())

    assert result.status == 200
    assert repository.status_updates == [
        {"booking_id": booking.id, "status": BookingStatus.FAILED}
    ]
    assert publisher.successful == []


@pytest.mark.asyncio
async def test_process_payment_notification_marks_reversed_without_event():
    booking = build_booking()
    use_case, repository, _provider, publisher = build_use_case(
        booking=booking,
        payment_status={"status_code": 3},
    )

    result = await use_case.execute(build_command())

    assert result.status == 200
    assert repository.status_updates == [
        {"booking_id": booking.id, "status": BookingStatus.REVERSED}
    ]
    assert publisher.successful == []


@pytest.mark.asyncio
async def test_process_payment_notification_marks_unknown_status_pending():
    booking = build_booking()
    use_case, repository, _provider, publisher = build_use_case(
        booking=booking,
        payment_status={"status_code": 0},
    )

    result = await use_case.execute(build_command())

    assert result.status == 200
    assert repository.status_updates == [
        {"booking_id": booking.id, "status": BookingStatus.PENDING}
    ]
    assert publisher.successful == []


@pytest.mark.asyncio
async def test_process_payment_notification_rejects_missing_required_parameters():
    use_case, repository, provider, publisher = build_use_case()

    result = await use_case.execute(
        ProcessPaymentNotificationCommand(
            payment_order_id=None,
            merchant_reference=None,
            notification_type=None,
        )
    )

    assert result.as_response() == {
        "orderNotificationType": "IPNCHANGE",
        "orderTrackingId": "",
        "orderMerchantReference": "",
        "status": 500,
    }
    assert repository.lookup_calls == []
    assert provider.calls == []
    assert publisher.successful == []


@pytest.mark.asyncio
async def test_process_payment_notification_returns_failure_when_booking_not_found():
    use_case, repository, provider, publisher = build_use_case(booking=None)

    result = await use_case.execute(build_command("missing-booking-1234567890"))

    assert result.as_response() == {
        "orderNotificationType": "IPNCHANGE",
        "orderTrackingId": "track_123",
        "orderMerchantReference": "missing-booking-1234567890",
        "status": 500,
    }
    assert repository.lookup_calls == ["missing-booking"]
    assert provider.calls == []
    assert publisher.successful == []


@pytest.mark.asyncio
async def test_process_payment_notification_marks_cancelled_on_processing_error():
    booking = build_booking()
    use_case, repository, _provider, publisher = build_use_case(
        booking=booking,
        error=RuntimeError("Provider unavailable"),
    )

    result = await use_case.execute(build_command())

    assert result.status == 500
    assert repository.status_updates == [
        {"booking_id": booking.id, "status": BookingStatus.CANCELLED}
    ]
    assert publisher.successful == []


@pytest.mark.asyncio
async def test_process_payment_notification_keeps_plain_uuid_reference_intact():
    booking = build_booking()
    reference = str(booking.id)
    use_case, repository, _provider, _publisher = build_use_case(
        booking=booking,
        payment_status={"status_code": 1},
    )

    result = await use_case.execute(build_command(reference))

    assert result.status == 200
    assert repository.lookup_calls == [reference]
