from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True)
class PaymentRefundCommand:
    confirmation_code: str
    amount: float
    remarks: str


@dataclass(frozen=True)
class RequestedPaymentRefund:
    status: str
    message: str
    confirmation_code: str

    def as_response(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "confirmation_code": self.confirmation_code,
        }


class RequestPaymentRefundError(Exception):
    pass


class PaymentRefundValidationError(RequestPaymentRefundError):
    pass


class PaymentRefundProcessingError(RequestPaymentRefundError):
    pass


class PaymentRefundProvider(Protocol):
    async def request_refund(
        self,
        *,
        confirmation_code: str,
        amount: float,
        username: str,
        remarks: str,
    ) -> dict[str, Any]: ...


class PaymentRefundEventPublisher(Protocol):
    def publish_refund_requested(
        self,
        *,
        confirmation_code: str,
        amount: float,
        remarks: str,
        initiated_by: str,
        user_id: UUID,
        provider_status: str | None,
        provider_message: str | None,
    ) -> None: ...


class RequestPaymentRefund:
    def __init__(
        self,
        *,
        refund_provider: PaymentRefundProvider,
        refund_event_publisher: PaymentRefundEventPublisher,
    ):
        self.refund_provider = refund_provider
        self.refund_event_publisher = refund_event_publisher

    async def execute(
        self,
        *,
        user_id: UUID,
        user_email: str,
        command: PaymentRefundCommand,
    ) -> RequestedPaymentRefund:
        provider_response = await self._request_refund_from_provider(
            user_email=user_email,
            command=command,
        )

        try:
            self.refund_event_publisher.publish_refund_requested(
                confirmation_code=command.confirmation_code,
                amount=command.amount,
                remarks=command.remarks,
                initiated_by=user_email,
                user_id=user_id,
                provider_status=provider_response.get("status"),
                provider_message=provider_response.get("message"),
            )
        except Exception as exc:
            raise PaymentRefundProcessingError(str(exc)) from exc

        return RequestedPaymentRefund(
            status=provider_response.get("status", ""),
            message=provider_response.get("message", "Unknown response from provider"),
            confirmation_code=command.confirmation_code,
        )

    async def _request_refund_from_provider(
        self,
        *,
        user_email: str,
        command: PaymentRefundCommand,
    ) -> dict[str, Any]:
        try:
            return await self.refund_provider.request_refund(
                confirmation_code=command.confirmation_code,
                amount=command.amount,
                username=user_email,
                remarks=command.remarks,
            )
        except PaymentRefundValidationError:
            raise
        except Exception as exc:
            raise PaymentRefundProcessingError(str(exc)) from exc
