from uuid import uuid4

import pytest

from backend.application.payments.process_pesapal_callback import (
    PENDING_PAYMENT_MESSAGE,
    PaymentCallbackBookingRecord,
    PaymentTransactionStatusError,
    ProcessPesapalCallbackCommand,
    ProcessPesapalPaymentCallback,
)
from backend.models.bookings import BookingStatus


DEFAULT_BOOKING = object()


class StubCallbackBookingRepository:
    def __init__(self, booking: PaymentCallbackBookingRecord | None):
        self.booking = booking
        self.lookup_calls = []
        self.status_updates = []

    def get_payment_callback_booking(
        self, booking_id: str
    ) -> PaymentCallbackBookingRecord | None:
        self.lookup_calls.append(booking_id)
        return self.booking

    def update_payment_booking_status(self, booking_id, status: str) -> None:
        self.status_updates.append({"booking_id": booking_id, "status": status})


class StubTransactionProvider:
    def __init__(self, transaction_status=None, error: Exception | None = None):
        self.transaction_status = transaction_status or {}
        self.error = error
        self.calls = []

    async def get_transaction_status(self, order_tracking_id: str):
        self.calls.append(order_tracking_id)
        if self.error:
            raise self.error
        return self.transaction_status


class StubPaymentEventPublisher:
    def __init__(self):
        self.successful = []
        self.failed = []

    def publish_payment_successful(self, **kwargs) -> None:
        self.successful.append(kwargs)

    def publish_payment_failed(self, **kwargs) -> None:
        self.failed.append(kwargs)


def build_booking() -> PaymentCallbackBookingRecord:
    return PaymentCallbackBookingRecord(
        id=uuid4(),
        user_id=uuid4(),
        user_email="traveler@example.com",
        pnr="ABC123",
    )


def build_use_case(
    *,
    booking=DEFAULT_BOOKING,
    transaction_status=None,
    error: Exception | None = None,
):
    repository = StubCallbackBookingRepository(
        build_booking() if booking is DEFAULT_BOOKING else booking
    )
    provider = StubTransactionProvider(transaction_status, error)
    publisher = StubPaymentEventPublisher()
    use_case = ProcessPesapalPaymentCallback(
        booking_repository=repository,
        transaction_provider=provider,
        event_publisher=publisher,
    )
    return use_case, repository, provider, publisher


def build_command(reference: str = "booking-id-1234567890"):
    return ProcessPesapalCallbackCommand(
        order_tracking_id="track_123",
        order_merchant_reference=reference,
    )


@pytest.mark.asyncio
async def test_process_pesapal_callback_marks_success_and_publishes_event():
    booking = build_booking()
    use_case, repository, provider, publisher = build_use_case(
        booking=booking,
        transaction_status={
            "status_code": 1,
            "payment_method": "Visa",
            "amount": 100,
            "confirmation_code": "CONFIRM123",
        },
    )

    result = await use_case.execute(build_command())

    assert result.as_response() == {
        "status": "success",
        "message": "Payment completed successfully",
        "order_tracking_id": "track_123",
        "payment_method": "Visa",
        "amount": 100,
        "confirmation_code": "CONFIRM123",
    }
    assert repository.lookup_calls == ["booking-id"]
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
    assert publisher.failed == []


@pytest.mark.asyncio
async def test_process_pesapal_callback_marks_failed_and_publishes_event():
    booking = build_booking()
    use_case, repository, _provider, publisher = build_use_case(
        booking=booking,
        transaction_status={
            "status_code": 2,
            "description": "Card declined",
        },
    )

    result = await use_case.execute(build_command())

    assert result.status == "failed"
    assert result.message == "Payment failed: Card declined"
    assert repository.status_updates == [
        {"booking_id": booking.id, "status": BookingStatus.FAILED}
    ]
    assert publisher.failed == [
        {
            "booking_id": booking.id,
            "user_id": booking.user_id,
            "pnr": booking.pnr,
            "reason": "Card declined",
        }
    ]


@pytest.mark.asyncio
async def test_process_pesapal_callback_returns_pending_for_missing_payment_details():
    booking = build_booking()
    use_case, repository, _provider, publisher = build_use_case(
        booking=booking,
        transaction_status={
            "status_code": 0,
            "error": {"code": "payment_details_not_found"},
        },
    )

    result = await use_case.execute(build_command())

    assert result.status == "pending"
    assert result.message == PENDING_PAYMENT_MESSAGE
    assert repository.status_updates == [
        {"booking_id": booking.id, "status": BookingStatus.PENDING}
    ]
    assert publisher.successful == []
    assert publisher.failed == []


@pytest.mark.asyncio
async def test_process_pesapal_callback_handles_pending_payment_error_without_update():
    booking = build_booking()
    use_case, repository, _provider, publisher = build_use_case(
        booking=booking,
        error=PaymentTransactionStatusError("Pending Payment"),
    )

    result = await use_case.execute(build_command())

    assert result.status == "pending"
    assert result.message == PENDING_PAYMENT_MESSAGE
    assert repository.status_updates == []
    assert publisher.successful == []
    assert publisher.failed == []


@pytest.mark.asyncio
async def test_process_pesapal_callback_marks_cancelled_on_processing_error():
    booking = build_booking()
    use_case, repository, _provider, _publisher = build_use_case(
        booking=booking,
        error=PaymentTransactionStatusError("Provider unavailable"),
    )

    result = await use_case.execute(build_command())

    assert result.status == "error"
    assert result.message == "Error processing callback: Provider unavailable"
    assert repository.status_updates == [
        {"booking_id": booking.id, "status": BookingStatus.CANCELLED}
    ]


@pytest.mark.asyncio
async def test_process_pesapal_callback_returns_error_when_booking_not_found():
    use_case, repository, provider, publisher = build_use_case(booking=None)

    result = await use_case.execute(build_command("missing-booking-1234567890"))

    assert result.as_response() == {
        "status": "error",
        "message": "Booking not found",
        "order_tracking_id": "track_123",
    }
    assert repository.lookup_calls == ["missing-booking"]
    assert provider.calls == []
    assert publisher.successful == []
    assert publisher.failed == []


@pytest.mark.asyncio
async def test_process_pesapal_callback_keeps_plain_uuid_reference_intact():
    booking = build_booking()
    reference = str(booking.id)
    use_case, repository, _provider, _publisher = build_use_case(
        booking=booking,
        transaction_status={"status_code": 3},
    )

    result = await use_case.execute(build_command(reference))

    assert result.status == "reversed"
    assert repository.lookup_calls == [reference]
    assert repository.status_updates == [
        {"booking_id": booking.id, "status": BookingStatus.REVERSED}
    ]
