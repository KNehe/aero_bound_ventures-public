from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from backend.application.payments.payment_status import PaymentStatusProvider
from backend.models.bookings import BookingStatus


@dataclass(frozen=True)
class PaymentNotificationBookingRecord:
    id: UUID
    user_id: UUID
    user_email: str
    pnr: str


@dataclass(frozen=True)
class ProcessPaymentNotificationCommand:
    payment_order_id: str | None
    merchant_reference: str | None
    notification_type: str | None = None


@dataclass(frozen=True)
class ProcessedPaymentNotification:
    payment_order_id: str
    merchant_reference: str
    status: int
    notification_type: str = "IPNCHANGE"

    def as_response(self) -> dict[str, Any]:
        return {
            "orderNotificationType": self.notification_type,
            "orderTrackingId": self.payment_order_id,
            "orderMerchantReference": self.merchant_reference,
            "status": self.status,
        }


class PaymentNotificationBookingRepository(Protocol):
    def get_payment_notification_booking(
        self, booking_id: str
    ) -> PaymentNotificationBookingRecord | None: ...

    def update_payment_booking_status(self, booking_id: UUID, status: str) -> None: ...


class PaymentNotificationEventPublisher(Protocol):
    def publish_payment_successful(
        self,
        *,
        booking_id: UUID,
        user_id: UUID,
        user_email: str,
        pnr: str,
    ) -> None: ...


class ProcessPaymentNotification:
    def __init__(
        self,
        *,
        booking_repository: PaymentNotificationBookingRepository,
        payment_status_provider: PaymentStatusProvider,
        event_publisher: PaymentNotificationEventPublisher,
    ):
        self.booking_repository = booking_repository
        self.payment_status_provider = payment_status_provider
        self.event_publisher = event_publisher

    async def execute(
        self, command: ProcessPaymentNotificationCommand
    ) -> ProcessedPaymentNotification:
        if not command.payment_order_id or not command.merchant_reference:
            return self._failure_response(command)

        booking = self.booking_repository.get_payment_notification_booking(
            self._extract_booking_id(command.merchant_reference)
        )
        if not booking:
            return self._failure_response(command)

        try:
            payment_status = await self.payment_status_provider.get_payment_status(
                command.payment_order_id
            )
            self._apply_payment_status(
                booking=booking,
                payment_status=payment_status,
            )
            return self._success_response(command)
        except Exception:
            self.booking_repository.update_payment_booking_status(
                booking.id, BookingStatus.CANCELLED
            )
            return self._failure_response(command)

    def _apply_payment_status(
        self,
        *,
        booking: PaymentNotificationBookingRecord,
        payment_status: dict[str, Any],
    ) -> None:
        status_code = payment_status.get("status_code")

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
    def _extract_booking_id(merchant_reference: str) -> str:
        booking_id, separator, suffix = merchant_reference.rpartition("-")
        if separator and suffix.isdigit():
            return booking_id
        return merchant_reference

    @staticmethod
    def _success_response(
        command: ProcessPaymentNotificationCommand,
    ) -> ProcessedPaymentNotification:
        return ProcessedPaymentNotification(
            payment_order_id=command.payment_order_id or "",
            merchant_reference=command.merchant_reference or "",
            status=200,
        )

    @staticmethod
    def _failure_response(
        command: ProcessPaymentNotificationCommand,
    ) -> ProcessedPaymentNotification:
        return ProcessedPaymentNotification(
            payment_order_id=command.payment_order_id or "",
            merchant_reference=command.merchant_reference or "",
            status=500,
        )
