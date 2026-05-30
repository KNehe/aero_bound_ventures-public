from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from backend.application.payments.payment_status import (
    PaymentStatusLookupError,
    PaymentStatusProvider,
)
from backend.models.bookings import BookingStatus


PENDING_PAYMENT_MESSAGE = (
    "Payment is pending. Please complete the payment or try again."
)


@dataclass(frozen=True)
class PaymentCallbackBookingRecord:
    id: UUID
    user_id: UUID
    user_email: str
    pnr: str


@dataclass(frozen=True)
class ProcessPaymentCallbackCommand:
    payment_order_id: str
    merchant_reference: str


@dataclass(frozen=True)
class ProcessedPaymentCallback:
    status: str
    message: str
    payment_order_id: str
    payment_method: Any | None = None
    amount: Any | None = None
    confirmation_code: Any | None = None

    def as_response(self) -> dict[str, Any]:
        response: dict[str, Any] = {
            "status": self.status,
            "message": self.message,
            "order_tracking_id": self.payment_order_id,
        }
        if self.payment_method is not None:
            response["payment_method"] = self.payment_method
        if self.amount is not None:
            response["amount"] = self.amount
        if self.confirmation_code is not None:
            response["confirmation_code"] = self.confirmation_code
        return response


class PaymentCallbackBookingRepository(Protocol):
    def get_payment_callback_booking(
        self, booking_id: str
    ) -> PaymentCallbackBookingRecord | None: ...

    def update_payment_booking_status(self, booking_id: UUID, status: str) -> None: ...


class PaymentCallbackEventPublisher(Protocol):
    def publish_payment_successful(
        self,
        *,
        booking_id: UUID,
        user_id: UUID,
        user_email: str,
        pnr: str,
    ) -> None: ...

    def publish_payment_failed(
        self,
        *,
        booking_id: UUID,
        user_id: UUID,
        pnr: str,
        reason: str,
    ) -> None: ...


class ProcessPaymentCallback:
    def __init__(
        self,
        *,
        booking_repository: PaymentCallbackBookingRepository,
        payment_status_provider: PaymentStatusProvider,
        event_publisher: PaymentCallbackEventPublisher,
    ):
        self.booking_repository = booking_repository
        self.payment_status_provider = payment_status_provider
        self.event_publisher = event_publisher

    async def execute(
        self, command: ProcessPaymentCallbackCommand
    ) -> ProcessedPaymentCallback:
        booking_id = self._extract_booking_id(command.merchant_reference)
        booking = self.booking_repository.get_payment_callback_booking(booking_id)
        if not booking:
            return ProcessedPaymentCallback(
                status="error",
                message="Booking not found",
                payment_order_id=command.payment_order_id,
            )

        try:
            payment_status = await self.payment_status_provider.get_payment_status(
                command.payment_order_id
            )
            return self._process_payment_status(
                booking=booking,
                payment_status=payment_status,
                payment_order_id=command.payment_order_id,
            )
        except PaymentStatusLookupError as exc:
            if "Pending Payment" in str(exc):
                return ProcessedPaymentCallback(
                    status="pending",
                    message=PENDING_PAYMENT_MESSAGE,
                    payment_order_id=command.payment_order_id,
                )
            return self._handle_processing_error(
                booking=booking,
                payment_order_id=command.payment_order_id,
                error=exc,
            )
        except Exception as exc:
            return self._handle_processing_error(
                booking=booking,
                payment_order_id=command.payment_order_id,
                error=exc,
            )

    def _process_payment_status(
        self,
        *,
        booking: PaymentCallbackBookingRecord,
        payment_status: dict[str, Any],
        payment_order_id: str,
    ) -> ProcessedPaymentCallback:
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
            return ProcessedPaymentCallback(
                status="success",
                message="Payment completed successfully",
                payment_order_id=payment_order_id,
                payment_method=payment_status.get("payment_method"),
                amount=payment_status.get("amount"),
                confirmation_code=payment_status.get("confirmation_code"),
            )

        if status_code == 2:
            self.booking_repository.update_payment_booking_status(
                booking.id, BookingStatus.FAILED
            )
            reason = payment_status.get("description", "Unknown error")
            self.event_publisher.publish_payment_failed(
                booking_id=booking.id,
                user_id=booking.user_id,
                pnr=booking.pnr,
                reason=reason,
            )
            return ProcessedPaymentCallback(
                status="failed",
                message=f"Payment failed: {reason}",
                payment_order_id=payment_order_id,
            )

        if status_code == 3:
            self.booking_repository.update_payment_booking_status(
                booking.id, BookingStatus.REVERSED
            )
            return ProcessedPaymentCallback(
                status="reversed",
                message="Payment was reversed",
                payment_order_id=payment_order_id,
            )

        self.booking_repository.update_payment_booking_status(
            booking.id, BookingStatus.PENDING
        )
        error = payment_status.get("error", {})
        if error and error.get("code") == "payment_details_not_found":
            return ProcessedPaymentCallback(
                status="pending",
                message=PENDING_PAYMENT_MESSAGE,
                payment_order_id=payment_order_id,
            )

        return ProcessedPaymentCallback(
            status="invalid",
            message=(
                "Invalid payment status: "
                f"{payment_status.get('payment_status_description', '')}"
            ),
            payment_order_id=payment_order_id,
        )

    def _handle_processing_error(
        self,
        *,
        booking: PaymentCallbackBookingRecord,
        payment_order_id: str,
        error: Exception,
    ) -> ProcessedPaymentCallback:
        self.booking_repository.update_payment_booking_status(
            booking.id, BookingStatus.CANCELLED
        )
        return ProcessedPaymentCallback(
            status="error",
            message=f"Error processing callback: {str(error)}",
            payment_order_id=payment_order_id,
        )

    @staticmethod
    def _extract_booking_id(merchant_reference: str) -> str:
        booking_id, separator, suffix = merchant_reference.rpartition("-")
        if separator and suffix.isdigit():
            return booking_id
        return merchant_reference
