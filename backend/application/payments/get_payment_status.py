from backend.application.payments.payment_status import (
    PaymentStatus,
    PaymentStatusLookupError,
    PaymentStatusProvider,
)


class GetPaymentStatusError(Exception):
    pass


class InvalidPaymentStatusRequest(GetPaymentStatusError):
    pass


class PaymentStatusProviderError(GetPaymentStatusError):
    pass


class GetPaymentStatus:
    def __init__(self, *, payment_status_provider: PaymentStatusProvider):
        self.payment_status_provider = payment_status_provider

    async def execute(self, payment_order_id: str) -> PaymentStatus:
        try:
            payment_status = await self.payment_status_provider.get_payment_status(
                payment_order_id
            )
        except PaymentStatusLookupError as exc:
            raise InvalidPaymentStatusRequest(str(exc)) from exc
        except Exception as exc:
            raise PaymentStatusProviderError(str(exc)) from exc

        return PaymentStatus.from_provider_response(payment_status)
