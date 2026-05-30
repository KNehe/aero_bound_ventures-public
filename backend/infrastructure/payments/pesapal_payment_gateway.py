from typing import Any, Protocol

from backend.application.payments.initiate_pesapal_payment import (
    InitiatedPesapalPayment,
    PaymentProviderValidationError,
)
from backend.application.payments.payment_status import PaymentStatusLookupError
from backend.application.payments.request_payment_refund import (
    PaymentRefundValidationError,
)


class PesapalClientProtocol(Protocol):
    ipn_id: str | None

    async def submit_order_request(
        self,
        merchant_reference: str,
        amount: float,
        currency: str,
        description: str,
        callback_url: str,
        notification_id: str,
        billing_address: dict[str, Any],
    ) -> dict[str, Any]: ...

    async def get_transaction_status(
        self, order_tracking_id: str
    ) -> dict[str, Any]: ...

    async def request_refund(
        self,
        confirmation_code: str,
        amount: float,
        username: str,
        remarks: str,
    ) -> dict[str, Any]: ...


class PesapalPaymentGateway:
    def __init__(self, client: PesapalClientProtocol):
        self.client = client

    def is_configured(self) -> bool:
        return bool(self.client.ipn_id)

    async def initiate_payment(
        self,
        *,
        merchant_reference: str,
        amount: float,
        currency: str,
        description: str,
        callback_url: str,
        billing_address: dict[str, str],
    ) -> InitiatedPesapalPayment:
        if not self.client.ipn_id:
            raise PaymentProviderValidationError("Payment notification ID is missing")

        try:
            result = await self.client.submit_order_request(
                merchant_reference=merchant_reference,
                amount=amount,
                currency=currency,
                description=description,
                callback_url=callback_url,
                notification_id=self.client.ipn_id,
                billing_address=billing_address,
            )
        except ValueError as exc:
            raise PaymentProviderValidationError(str(exc)) from exc

        return InitiatedPesapalPayment(
            order_tracking_id=result["order_tracking_id"],
            merchant_reference=result["merchant_reference"],
            redirect_url=result["redirect_url"],
            status=result.get("status"),
        )

    async def get_transaction_status(self, order_tracking_id: str) -> dict[str, Any]:
        try:
            return await self.client.get_transaction_status(order_tracking_id)
        except ValueError as exc:
            raise PaymentStatusLookupError(str(exc)) from exc

    async def request_refund(
        self,
        *,
        confirmation_code: str,
        amount: float,
        username: str,
        remarks: str,
    ) -> dict[str, Any]:
        try:
            return await self.client.request_refund(
                confirmation_code=confirmation_code,
                amount=amount,
                username=username,
                remarks=remarks,
            )
        except ValueError as exc:
            raise PaymentRefundValidationError(str(exc)) from exc
