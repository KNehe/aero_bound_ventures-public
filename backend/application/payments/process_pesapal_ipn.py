from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from backend.models.bookings import BookingStatus


@dataclass(frozen=True)
class PaymentIpnBookingRecord:
    id: UUID
    user_id: UUID
    user_email: str
    pnr: str


@dataclass(frozen=True)
class ProcessPesapalIpnCommand:
    order_tracking_id: str | None
    order_merchant_reference: str | None
    order_notification_type: str | None = None


@dataclass(frozen=True)
class ProcessedPesapalIpn:
    order_tracking_id: str
    order_merchant_reference: str
    status: int
    order_notification_type: str = "IPNCHANGE"

    def as_response(self) -> dict[str, Any]:
        return {
            "orderNotificationType": self.order_notification_type,
            "orderTrackingId": self.order_tracking_id,
            "orderMerchantReference": self.order_merchant_reference,
            "status": self.status,
        }


class PaymentIpnBookingRepository(Protocol):
    def get_payment_ipn_booking(
        self, booking_id: str
    ) -> PaymentIpnBookingRecord | None: ...

    def update_payment_booking_status(self, booking_id: UUID, status: str) -> None: ...


class PaymentIpnTransactionStatusProvider(Protocol):
    async def get_transaction_status(
        self, order_tracking_id: str
    ) -> dict[str, Any]: ...


class PaymentIpnEventPublisher(Protocol):
    def publish_payment_successful(
        self,
        *,
        booking_id: UUID,
        user_id: UUID,
        user_email: str,
        pnr: str,
    ) -> None: ...


class ProcessPesapalIpn:
    def __init__(
        self,
        *,
        booking_repository: PaymentIpnBookingRepository,
        transaction_provider: PaymentIpnTransactionStatusProvider,
        event_publisher: PaymentIpnEventPublisher,
    ):
        self.booking_repository = booking_repository
        self.transaction_provider = transaction_provider
        self.event_publisher = event_publisher

    async def execute(self, command: ProcessPesapalIpnCommand) -> ProcessedPesapalIpn:
        if not command.order_tracking_id or not command.order_merchant_reference:
            return self._failure_response(command)

        booking = self.booking_repository.get_payment_ipn_booking(
            self._extract_booking_id(command.order_merchant_reference)
        )
        if not booking:
            return self._failure_response(command)

        try:
            transaction_status = await self.transaction_provider.get_transaction_status(
                command.order_tracking_id
            )
            self._apply_transaction_status(
                booking=booking,
                transaction_status=transaction_status,
            )
            return self._success_response(command)
        except Exception:
            self.booking_repository.update_payment_booking_status(
                booking.id, BookingStatus.CANCELLED
            )
            return self._failure_response(command)

    def _apply_transaction_status(
        self,
        *,
        booking: PaymentIpnBookingRecord,
        transaction_status: dict[str, Any],
    ) -> None:
        status_code = transaction_status.get("status_code")

        if status_code == 1:
            self.booking_repository.update_payment_booking_status(
                booking.id, BookingStatus.PAID
            )
            self.event_publisher.publish_payment_successful(
                booking_id=booking.id,
                user_id=booking.user_id,
                user_email=booking.user_email,
                pnr=booking.pnr,
            )
            return

        if status_code == 2:
            self.booking_repository.update_payment_booking_status(
                booking.id, BookingStatus.FAILED
            )
            return

        if status_code == 3:
            self.booking_repository.update_payment_booking_status(
                booking.id, BookingStatus.REVERSED
            )
            return

        self.booking_repository.update_payment_booking_status(
            booking.id, BookingStatus.PENDING
        )

    @staticmethod
    def _extract_booking_id(order_merchant_reference: str) -> str:
        booking_id, separator, suffix = order_merchant_reference.rpartition("-")
        if separator and suffix.isdigit():
            return booking_id
        return order_merchant_reference

    @staticmethod
    def _success_response(command: ProcessPesapalIpnCommand) -> ProcessedPesapalIpn:
        return ProcessedPesapalIpn(
            order_tracking_id=command.order_tracking_id or "",
            order_merchant_reference=command.order_merchant_reference or "",
            status=200,
        )

    @staticmethod
    def _failure_response(command: ProcessPesapalIpnCommand) -> ProcessedPesapalIpn:
        return ProcessedPesapalIpn(
            order_tracking_id=command.order_tracking_id or "",
            order_merchant_reference=command.order_merchant_reference or "",
            status=500,
        )
