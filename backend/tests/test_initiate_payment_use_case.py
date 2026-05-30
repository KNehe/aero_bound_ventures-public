from uuid import uuid4

import pytest

from backend.application.payments.initiate_payment import (
    InitiatePayment,
    InitiatePaymentCommand,
    InitiatedPayment,
    PaymentBillingAddress,
    PaymentBookingAccessDenied,
    PaymentBookingAlreadyPaid,
    PaymentBookingNotFound,
    PaymentBookingRecord,
    PaymentSystemNotConfigured,
)
from backend.models.bookings import BookingStatus


class StubBookingRepository:
    def __init__(self, booking: PaymentBookingRecord | None):
        self.booking = booking
        self.calls = []

    def get_payment_booking(self, booking_id: str) -> PaymentBookingRecord | None:
        self.calls.append(booking_id)
        return self.booking


class StubPaymentProvider:
    def __init__(self, *, configured: bool = True):
        self.configured = configured
        self.calls = []

    def is_configured(self) -> bool:
        return self.configured

    async def initiate_payment(self, **kwargs):
        self.calls.append(kwargs)
        return InitiatedPayment(
            payment_order_id="track_123",
            merchant_reference=kwargs["merchant_reference"],
            redirect_url="https://payment.example.com/pay/123",
            status="200",
        )


def build_command(**overrides) -> InitiatePaymentCommand:
    values = {
        "booking_id": "booking_123",
        "amount": 125.5,
        "currency": "USD",
        "description": "Flight booking ABC123",
        "callback_url": "https://frontend.example.com/payment/callback",
        "billing_address": PaymentBillingAddress(
            email_address="traveler@example.com",
            phone_number="5551234",
            country_code="1",
            first_name="Test",
            last_name="Traveler",
        ),
    }
    values.update(overrides)
    return InitiatePaymentCommand(**values)


@pytest.mark.asyncio
async def test_initiate_payment_builds_provider_request():
    user_id = uuid4()
    booking_id = uuid4()
    repository = StubBookingRepository(
        PaymentBookingRecord(
            id=booking_id,
            user_id=user_id,
            status=BookingStatus.CONFIRMED,
        )
    )
    provider = StubPaymentProvider()
    use_case = InitiatePayment(
        booking_repository=repository,
        payment_initiation_provider=provider,
        default_callback_url="https://default.example.com/payment/callback",
    )

    result = await use_case.execute(user_id=user_id, command=build_command())

    assert result.redirect_url == "https://payment.example.com/pay/123"
    assert repository.calls == ["booking_123"]
    assert provider.calls == [
        {
            "merchant_reference": str(booking_id),
            "amount": 125.5,
            "currency": "USD",
            "description": f"Flight booking payment - {booking_id}",
            "callback_url": "https://frontend.example.com/payment/callback",
            "billing_address": {
                "email_address": "traveler@example.com",
                "phone_number": "5551234",
                "country_code": "1",
                "first_name": "Test",
                "middle_name": "",
                "last_name": "Traveler",
                "line_1": "",
                "line_2": "",
                "city": "",
                "state": "",
                "postal_code": "",
                "zip_code": "",
            },
        }
    ]


@pytest.mark.asyncio
async def test_initiate_payment_uses_default_callback_when_missing():
    user_id = uuid4()
    repository = StubBookingRepository(
        PaymentBookingRecord(
            id=uuid4(),
            user_id=user_id,
            status=BookingStatus.CONFIRMED,
        )
    )
    provider = StubPaymentProvider()
    use_case = InitiatePayment(
        booking_repository=repository,
        payment_initiation_provider=provider,
        default_callback_url="https://default.example.com/payment/callback",
    )

    await use_case.execute(user_id=user_id, command=build_command(callback_url=""))

    assert provider.calls[0]["callback_url"] == (
        "https://default.example.com/payment/callback"
    )


@pytest.mark.asyncio
async def test_initiate_payment_rejects_missing_booking():
    use_case = InitiatePayment(
        booking_repository=StubBookingRepository(None),
        payment_initiation_provider=StubPaymentProvider(),
        default_callback_url="https://default.example.com/payment/callback",
    )

    with pytest.raises(PaymentBookingNotFound):
        await use_case.execute(user_id=uuid4(), command=build_command())


@pytest.mark.asyncio
async def test_initiate_payment_rejects_other_users_booking():
    repository = StubBookingRepository(
        PaymentBookingRecord(
            id=uuid4(),
            user_id=uuid4(),
            status=BookingStatus.CONFIRMED,
        )
    )
    provider = StubPaymentProvider()
    use_case = InitiatePayment(
        booking_repository=repository,
        payment_initiation_provider=provider,
        default_callback_url="https://default.example.com/payment/callback",
    )

    with pytest.raises(PaymentBookingAccessDenied):
        await use_case.execute(user_id=uuid4(), command=build_command())

    assert provider.calls == []


@pytest.mark.asyncio
async def test_initiate_payment_rejects_paid_booking():
    user_id = uuid4()
    repository = StubBookingRepository(
        PaymentBookingRecord(
            id=uuid4(),
            user_id=user_id,
            status=BookingStatus.PAID,
        )
    )
    provider = StubPaymentProvider()
    use_case = InitiatePayment(
        booking_repository=repository,
        payment_initiation_provider=provider,
        default_callback_url="https://default.example.com/payment/callback",
    )

    with pytest.raises(PaymentBookingAlreadyPaid):
        await use_case.execute(user_id=user_id, command=build_command())

    assert provider.calls == []


@pytest.mark.asyncio
async def test_initiate_payment_requires_configured_provider():
    user_id = uuid4()
    repository = StubBookingRepository(
        PaymentBookingRecord(
            id=uuid4(),
            user_id=user_id,
            status=BookingStatus.CONFIRMED,
        )
    )
    provider = StubPaymentProvider(configured=False)
    use_case = InitiatePayment(
        booking_repository=repository,
        payment_initiation_provider=provider,
        default_callback_url="https://default.example.com/payment/callback",
    )

    with pytest.raises(PaymentSystemNotConfigured):
        await use_case.execute(user_id=user_id, command=build_command())

    assert provider.calls == []
