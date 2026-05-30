import pytest

from backend.application.payments.get_payment_status import (
    GetPaymentStatus,
    InvalidPaymentStatusRequest,
    PaymentStatusProviderError,
)
from backend.application.payments.payment_status import PaymentStatusLookupError


class StubTransactionStatusProvider:
    def __init__(self, transaction_status=None, error: Exception | None = None):
        self.transaction_status = transaction_status or {}
        self.error = error
        self.calls = []

    async def get_transaction_status(self, order_tracking_id: str):
        self.calls.append(order_tracking_id)
        if self.error:
            raise self.error
        return self.transaction_status


@pytest.mark.asyncio
async def test_get_payment_status_maps_provider_response():
    provider = StubTransactionStatusProvider(
        {
            "payment_method": "Visa",
            "amount": 100,
            "created_date": "2026-05-30T10:00:00Z",
            "confirmation_code": "CONFIRM123",
            "payment_status_description": "Completed",
            "description": "Payment completed",
            "message": "Request processed successfully",
            "payment_account": "476173**0010",
            "call_back_url": "https://frontend.com/callback",
            "status_code": 1,
            "merchant_reference": "booking_123",
            "payment_status_code": "COMPLETED",
            "currency": "USD",
        }
    )
    use_case = GetPaymentStatus(payment_status_provider=provider)

    result = await use_case.execute("track_123")

    assert provider.calls == ["track_123"]
    assert result.as_response() == {
        "payment_method": "Visa",
        "amount": 100,
        "created_date": "2026-05-30T10:00:00Z",
        "confirmation_code": "CONFIRM123",
        "payment_status_description": "Completed",
        "description": "Payment completed",
        "message": "Request processed successfully",
        "payment_account": "476173**0010",
        "call_back_url": "https://frontend.com/callback",
        "status_code": 1,
        "merchant_reference": "booking_123",
        "payment_status_code": "COMPLETED",
        "currency": "USD",
        "error": None,
    }


@pytest.mark.asyncio
async def test_get_payment_status_supplies_schema_safe_defaults():
    provider = StubTransactionStatusProvider({})
    use_case = GetPaymentStatus(payment_status_provider=provider)

    result = await use_case.execute("track_123")

    assert result.as_response() == {
        "payment_method": "",
        "amount": 0,
        "created_date": "",
        "confirmation_code": "",
        "payment_status_description": "",
        "description": "",
        "message": "",
        "payment_account": "",
        "call_back_url": "",
        "status_code": 0,
        "merchant_reference": "",
        "payment_status_code": "",
        "currency": "USD",
        "error": None,
    }


@pytest.mark.asyncio
async def test_get_payment_status_translates_provider_validation_error():
    provider = StubTransactionStatusProvider(
        error=PaymentStatusLookupError("Invalid order tracking id")
    )
    use_case = GetPaymentStatus(payment_status_provider=provider)

    with pytest.raises(InvalidPaymentStatusRequest) as exc_info:
        await use_case.execute("bad_track")

    assert str(exc_info.value) == "Invalid order tracking id"


@pytest.mark.asyncio
async def test_get_payment_status_translates_unexpected_provider_error():
    provider = StubTransactionStatusProvider(error=RuntimeError("Provider unavailable"))
    use_case = GetPaymentStatus(payment_status_provider=provider)

    with pytest.raises(PaymentStatusProviderError) as exc_info:
        await use_case.execute("track_123")

    assert str(exc_info.value) == "Provider unavailable"
