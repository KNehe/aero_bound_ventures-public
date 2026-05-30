from uuid import uuid4

import pytest

from backend.application.payments.request_payment_refund import (
    PaymentRefundCommand,
    PaymentRefundProcessingError,
    PaymentRefundValidationError,
    RequestPaymentRefund,
)


class StubRefundProvider:
    def __init__(self, response=None, error: Exception | None = None):
        self.response = response or {}
        self.error = error
        self.calls = []

    async def request_refund(
        self,
        *,
        confirmation_code: str,
        amount: float,
        username: str,
        remarks: str,
    ):
        self.calls.append(
            {
                "confirmation_code": confirmation_code,
                "amount": amount,
                "username": username,
                "remarks": remarks,
            }
        )
        if self.error:
            raise self.error
        return self.response


class StubRefundEventPublisher:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.refund_requested = []

    def publish_refund_requested(self, **kwargs) -> None:
        if self.error:
            raise self.error
        self.refund_requested.append(kwargs)


def build_command() -> PaymentRefundCommand:
    return PaymentRefundCommand(
        confirmation_code="CONFIRM123",
        amount=25.5,
        remarks="Customer requested itinerary change",
    )


@pytest.mark.asyncio
async def test_request_payment_refund_requests_provider_and_publishes_event():
    user_id = uuid4()
    provider = StubRefundProvider(
        {
            "status": "200",
            "message": "Refund request submitted",
        }
    )
    publisher = StubRefundEventPublisher()
    use_case = RequestPaymentRefund(
        refund_provider=provider,
        refund_event_publisher=publisher,
    )

    result = await use_case.execute(
        user_id=user_id,
        user_email="traveler@example.com",
        command=build_command(),
    )

    assert provider.calls == [
        {
            "confirmation_code": "CONFIRM123",
            "amount": 25.5,
            "username": "traveler@example.com",
            "remarks": "Customer requested itinerary change",
        }
    ]
    assert publisher.refund_requested == [
        {
            "confirmation_code": "CONFIRM123",
            "amount": 25.5,
            "remarks": "Customer requested itinerary change",
            "initiated_by": "traveler@example.com",
            "user_id": user_id,
            "provider_status": "200",
            "provider_message": "Refund request submitted",
        }
    ]
    assert result.as_response() == {
        "status": "200",
        "message": "Refund request submitted",
        "confirmation_code": "CONFIRM123",
    }


@pytest.mark.asyncio
async def test_request_payment_refund_preserves_provider_rejection_response():
    provider = StubRefundProvider(
        {
            "status": "500",
            "message": "Refund rejected",
        }
    )
    publisher = StubRefundEventPublisher()
    use_case = RequestPaymentRefund(
        refund_provider=provider,
        refund_event_publisher=publisher,
    )

    result = await use_case.execute(
        user_id=uuid4(),
        user_email="traveler@example.com",
        command=build_command(),
    )

    assert result.status == "500"
    assert result.message == "Refund rejected"
    assert len(publisher.refund_requested) == 1


@pytest.mark.asyncio
async def test_request_payment_refund_translates_provider_validation_error():
    provider = StubRefundProvider(
        error=PaymentRefundValidationError("Invalid confirmation code")
    )
    use_case = RequestPaymentRefund(
        refund_provider=provider,
        refund_event_publisher=StubRefundEventPublisher(),
    )

    with pytest.raises(PaymentRefundValidationError) as exc_info:
        await use_case.execute(
            user_id=uuid4(),
            user_email="traveler@example.com",
            command=build_command(),
        )

    assert str(exc_info.value) == "Invalid confirmation code"


@pytest.mark.asyncio
async def test_request_payment_refund_translates_provider_processing_error():
    provider = StubRefundProvider(error=RuntimeError("Provider unavailable"))
    use_case = RequestPaymentRefund(
        refund_provider=provider,
        refund_event_publisher=StubRefundEventPublisher(),
    )

    with pytest.raises(PaymentRefundProcessingError) as exc_info:
        await use_case.execute(
            user_id=uuid4(),
            user_email="traveler@example.com",
            command=build_command(),
        )

    assert str(exc_info.value) == "Provider unavailable"


@pytest.mark.asyncio
async def test_request_payment_refund_translates_event_publish_error():
    provider = StubRefundProvider(
        {
            "status": "200",
            "message": "Refund request submitted",
        }
    )
    use_case = RequestPaymentRefund(
        refund_provider=provider,
        refund_event_publisher=StubRefundEventPublisher(
            error=RuntimeError("Kafka unavailable")
        ),
    )

    with pytest.raises(PaymentRefundProcessingError) as exc_info:
        await use_case.execute(
            user_id=uuid4(),
            user_email="traveler@example.com",
            command=build_command(),
        )

    assert str(exc_info.value) == "Kafka unavailable"
