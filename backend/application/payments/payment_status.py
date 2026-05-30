from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class PaymentStatus:
    payment_method: str
    amount: float
    created_date: str
    confirmation_code: str
    payment_status_description: str
    description: str
    message: str
    payment_account: str
    call_back_url: str
    status_code: int
    merchant_reference: str
    payment_status_code: str
    currency: str
    error: dict[str, Any] | None = None

    @classmethod
    def from_provider_response(cls, data: dict[str, Any]) -> "PaymentStatus":
        return cls(
            payment_method=data.get("payment_method", ""),
            amount=data.get("amount", 0),
            created_date=data.get("created_date", ""),
            confirmation_code=data.get("confirmation_code", ""),
            payment_status_description=data.get("payment_status_description", ""),
            description=data.get("description", ""),
            message=data.get("message", ""),
            payment_account=data.get("payment_account", ""),
            call_back_url=data.get("call_back_url", ""),
            status_code=data.get("status_code", 0),
            merchant_reference=data.get("merchant_reference", ""),
            payment_status_code=data.get("payment_status_code", ""),
            currency=data.get("currency", "USD"),
            error=data.get("error"),
        )

    def as_response(self) -> dict[str, Any]:
        return {
            "payment_method": self.payment_method,
            "amount": self.amount,
            "created_date": self.created_date,
            "confirmation_code": self.confirmation_code,
            "payment_status_description": self.payment_status_description,
            "description": self.description,
            "message": self.message,
            "payment_account": self.payment_account,
            "call_back_url": self.call_back_url,
            "status_code": self.status_code,
            "merchant_reference": self.merchant_reference,
            "payment_status_code": self.payment_status_code,
            "currency": self.currency,
            "error": self.error,
        }


class PaymentStatusLookupError(Exception):
    pass


class PaymentStatusProvider(Protocol):
    async def get_transaction_status(
        self, order_tracking_id: str
    ) -> dict[str, Any]: ...
