from typing import Protocol
from uuid import UUID

from backend.utils.constants import KafkaEventTypes, KafkaTopics


class KafkaProducerProtocol(Protocol):
    def send(self, topic: str, payload: dict) -> None: ...


class KafkaPaymentEventPublisher:
    def __init__(self, producer: KafkaProducerProtocol):
        self.producer = producer

    def publish_payment_successful(
        self,
        *,
        booking_id: UUID,
        user_id: UUID,
        user_email: str,
        pnr: str,
    ) -> None:
        self.producer.send(
            KafkaTopics.PAYMENT_EVENTS,
            {
                "event_type": KafkaEventTypes.PAYMENT_SUCCESSFUL,
                "booking_id": str(booking_id),
                "pnr": pnr,
                "user_email": user_email,
                "user_id": str(user_id),
            },
        )

    def publish_payment_failed(
        self,
        *,
        booking_id: UUID,
        user_id: UUID,
        pnr: str,
        reason: str,
    ) -> None:
        self.producer.send(
            KafkaTopics.PAYMENT_EVENTS,
            {
                "event_type": KafkaEventTypes.PAYMENT_FAILED,
                "booking_id": str(booking_id),
                "pnr": pnr,
                "user_id": str(user_id),
                "reason": reason,
            },
        )

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
    ) -> None:
        self.producer.send(
            KafkaTopics.PAYMENT_EVENTS,
            {
                "event_type": KafkaEventTypes.REFUND_REQUESTED,
                "confirmation_code": confirmation_code,
                "amount": amount,
                "remarks": remarks,
                "initiated_by": initiated_by,
                "user_id": str(user_id),
                "pesapal_status": provider_status,
                "pesapal_message": provider_message,
            },
        )
