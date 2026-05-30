from uuid import UUID

from backend.utils.constants import KafkaEventTypes, KafkaTopics
from backend.utils.kafka import KafkaProducer


class KafkaBookingEventPublisher:
    def __init__(self, producer: KafkaProducer):
        self.producer = producer

    def publish_booking_created(
        self,
        *,
        booking_id: UUID,
        user_id: UUID,
        pnr: str,
        user_email: str,
    ) -> None:
        self.producer.send(
            KafkaTopics.BOOKING_EVENTS,
            {
                "event_type": KafkaEventTypes.BOOKING_CREATED,
                "booking_id": str(booking_id),
                "user_id": str(user_id),
                "pnr": pnr,
                "user_email": user_email,
            },
        )

    def publish_booking_cancelled(
        self,
        *,
        booking_id: UUID,
        user_id: UUID,
        pnr: str | None,
        user_email: str,
    ) -> None:
        self.producer.send(
            KafkaTopics.BOOKING_EVENTS,
            {
                "event_type": KafkaEventTypes.BOOKING_CANCELLED,
                "booking_id": str(booking_id),
                "user_id": str(user_id),
                "pnr": pnr,
                "user_email": user_email,
            },
        )
