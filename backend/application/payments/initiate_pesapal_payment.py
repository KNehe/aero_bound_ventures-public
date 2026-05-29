from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from backend.models.bookings import BookingStatus


@dataclass(frozen=True)
class PaymentBookingRecord:
    id: UUID
    user_id: UUID
    status: str


@dataclass(frozen=True)
class PaymentBillingAddress:
    email_address: str
    phone_number: str | None = None
    country_code: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    line_1: str | None = None
    line_2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    zip_code: str | None = None


@dataclass(frozen=True)
class InitiatePesapalPaymentCommand:
    booking_id: str
    amount: float
    currency: str
    description: str
    callback_url: str | None
    billing_address: PaymentBillingAddress


@dataclass(frozen=True)
class InitiatedPesapalPayment:
    order_tracking_id: str
    merchant_reference: str
    redirect_url: str
    status: str | None = None


class InitiatePesapalPaymentError(Exception):
    pass


class PaymentBookingNotFound(InitiatePesapalPaymentError):
    pass


class PaymentBookingAccessDenied(InitiatePesapalPaymentError):
    pass


class PaymentBookingAlreadyPaid(InitiatePesapalPaymentError):
    pass


class PaymentSystemNotConfigured(InitiatePesapalPaymentError):
    pass


class PaymentProviderValidationError(InitiatePesapalPaymentError):
    pass


class PaymentBookingRepository(Protocol):
    def get_payment_booking(self, booking_id: str) -> PaymentBookingRecord | None: ...


class PesapalPaymentProvider(Protocol):
    def is_configured(self) -> bool: ...

    async def initiate_payment(
        self,
        *,
        merchant_reference: str,
        amount: float,
        currency: str,
        description: str,
        callback_url: str,
        billing_address: dict[str, str],
    ) -> InitiatedPesapalPayment: ...


class InitiatePesapalPayment:
    def __init__(
        self,
        *,
        booking_repository: PaymentBookingRepository,
        payment_provider: PesapalPaymentProvider,
        default_callback_url: str,
    ):
        self.booking_repository = booking_repository
        self.payment_provider = payment_provider
        self.default_callback_url = default_callback_url

    async def execute(
        self,
        *,
        user_id: UUID,
        command: InitiatePesapalPaymentCommand,
    ) -> InitiatedPesapalPayment:
        booking = self.booking_repository.get_payment_booking(command.booking_id)
        if not booking:
            raise PaymentBookingNotFound

        if booking.user_id != user_id:
            raise PaymentBookingAccessDenied

        if booking.status == BookingStatus.PAID:
            raise PaymentBookingAlreadyPaid

        if not self.payment_provider.is_configured():
            raise PaymentSystemNotConfigured

        return await self.payment_provider.initiate_payment(
            merchant_reference=str(booking.id),
            amount=command.amount,
            currency=command.currency,
            description=f"Flight booking payment - {booking.id}",
            callback_url=command.callback_url or self.default_callback_url,
            billing_address=self._billing_address_payload(command.billing_address),
        )

    @staticmethod
    def _billing_address_payload(address: PaymentBillingAddress) -> dict[str, str]:
        return {
            "email_address": address.email_address,
            "phone_number": address.phone_number or "",
            "country_code": address.country_code or "",
            "first_name": address.first_name or "",
            "middle_name": address.middle_name or "",
            "last_name": address.last_name or "",
            "line_1": address.line_1 or "",
            "line_2": address.line_2 or "",
            "city": address.city or "",
            "state": address.state or "",
            "postal_code": address.postal_code or "",
            "zip_code": address.zip_code or "",
        }
