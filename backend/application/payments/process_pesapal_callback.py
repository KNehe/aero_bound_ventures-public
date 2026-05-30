from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

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
class ProcessPesapalCallbackCommand:
    order_tracking_id: str
    order_merchant_reference: str


@dataclass(frozen=True)
class ProcessedPesapalCallback:
    status: str
    message: str
    order_tracking_id: str
    payment_method: Any | None = None
    amount: Any | None = None
    confirmation_code: Any | None = None

    def as_response(self) -> dict[str, Any]:
        response: dict[str, Any] = {
            "status": self.status,
            "message": self.message,
            "order_tracking_id": self.order_tracking_id,
        }
        if self.payment_method is not None:
            response["payment_method"] = self.payment_method
        if self.amount is not None:
            response["amount"] = self.amount
        if self.confirmation_code is not None:
            response["confirmation_code"] = self.confirmation_code
        return response


class PaymentTransactionStatusError(Exception):
    pass


class PaymentCallbackBookingRepository(Protocol):
    def get_payment_callback_booking(
        self, booking_id: str
    ) -> PaymentCallbackBookingRecord | None: ...

    def update_payment_booking_status(self, booking_id: UUID, status: str) -> None: ...


class PaymentTransactionStatusProvider(Protocol):
    async def get_transaction_status(
        self, order_tracking_id: str
    ) -> dict[str, Any]: ...


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


class ProcessPesapalPaymentCallback:
    def __init__(
        self,
        *,
        booking_repository: PaymentCallbackBookingRepository,
        transaction_provider: PaymentTransactionStatusProvider,
        event_publisher: PaymentCallbackEventPublisher,
    ):
        self.booking_repository = booking_repository
        self.transaction_provider = transaction_provider
        self.event_publisher = event_publisher

    async def execute(
        self, command: ProcessPesapalCallbackCommand
    ) -> ProcessedPesapalCallback:
        booking_id = self._extract_booking_id(command.order_merchant_reference)
        booking = self.booking_repository.get_payment_callback_booking(booking_id)
        if not booking:
            return ProcessedPesapalCallback(
                status="error",
                message="Booking not found",
                order_tracking_id=command.order_tracking_id,
            )

        try:
            transaction_status = await self.transaction_provider.get_transaction_status(
                command.order_tracking_id
            )
            return self._process_transaction_status(
                booking=booking,
                transaction_status=transaction_status,
                order_tracking_id=command.order_tracking_id,
            )
        except PaymentTransactionStatusError as exc:
            if "Pending Payment" in str(exc):
                return ProcessedPesapalCallback(
                    status="pending",
                    message=PENDING_PAYMENT_MESSAGE,
                    order_tracking_id=command.order_tracking_id,
                )
            return self._handle_processing_error(
                booking=booking,
                order_tracking_id=command.order_tracking_id,
                error=exc,
            )
        except Exception as exc:
            return self._handle_processing_error(
                booking=booking,
                order_tracking_id=command.order_tracking_id,
                error=exc,
            )

    def _process_transaction_status(
        self,
        *,
        booking: PaymentCallbackBookingRecord,
        transaction_status: dict[str, Any],
        order_tracking_id: str,
    ) -> ProcessedPesapalCallback:
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
            return ProcessedPesapalCallback(
                status="success",
                message="Payment completed successfully",
                order_tracking_id=order_tracking_id,
                payment_method=transaction_status.get("payment_method"),
                amount=transaction_status.get("amount"),
                confirmation_code=transaction_status.get("confirmation_code"),
            )

        if status_code == 2:
            self.booking_repository.update_payment_booking_status(
                booking.id, BookingStatus.FAILED
            )
            reason = transaction_status.get("description", "Unknown error")
            self.event_publisher.publish_payment_failed(
                booking_id=booking.id,
                user_id=booking.user_id,
                pnr=booking.pnr,
                reason=reason,
            )
            return ProcessedPesapalCallback(
                status="failed",
                message=f"Payment failed: {reason}",
                order_tracking_id=order_tracking_id,
            )

        if status_code == 3:
            self.booking_repository.update_payment_booking_status(
                booking.id, BookingStatus.REVERSED
            )
            return ProcessedPesapalCallback(
                status="reversed",
                message="Payment was reversed",
                order_tracking_id=order_tracking_id,
            )

        self.booking_repository.update_payment_booking_status(
            booking.id, BookingStatus.PENDING
        )
        error = transaction_status.get("error", {})
        if error and error.get("code") == "payment_details_not_found":
            return ProcessedPesapalCallback(
                status="pending",
                message=PENDING_PAYMENT_MESSAGE,
                order_tracking_id=order_tracking_id,
            )

        return ProcessedPesapalCallback(
            status="invalid",
            message=(
                "Invalid payment status: "
                f"{transaction_status.get('payment_status_description', '')}"
            ),
            order_tracking_id=order_tracking_id,
        )

    def _handle_processing_error(
        self,
        *,
        booking: PaymentCallbackBookingRecord,
        order_tracking_id: str,
        error: Exception,
    ) -> ProcessedPesapalCallback:
        self.booking_repository.update_payment_booking_status(
            booking.id, BookingStatus.CANCELLED
        )
        return ProcessedPesapalCallback(
            status="error",
            message=f"Error processing callback: {str(error)}",
            order_tracking_id=order_tracking_id,
        )

    @staticmethod
    def _extract_booking_id(order_merchant_reference: str) -> str:
        booking_id, separator, suffix = order_merchant_reference.rpartition("-")
        if separator and suffix.isdigit():
            return booking_id
        return order_merchant_reference
