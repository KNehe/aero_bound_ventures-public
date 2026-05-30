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

    async def execute(self, order_tracking_id: str) -> PaymentStatus:
        try:
            transaction_status = (
                await self.payment_status_provider.get_transaction_status(
                    order_tracking_id
                )
            )
        except PaymentStatusLookupError as exc:
            raise InvalidPaymentStatusRequest(str(exc)) from exc
        except Exception as exc:
            raise PaymentStatusProviderError(str(exc)) from exc

        return PaymentStatus.from_provider_response(transaction_status)
