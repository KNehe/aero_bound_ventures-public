from uuid import UUID

from backend.utils.constants import KafkaEventTypes, KafkaTopics
from backend.utils.kafka import KafkaProducer


class KafkaTicketEventPublisher:
    def __init__(self, producer: KafkaProducer):
        self.producer = producer

    def publish_ticket_uploaded(
        self,
        *,
        pnr: str,
        booking_id: UUID,
        user_id: UUID,
        user_email: str,
    ) -> None:
        self.producer.send(
            KafkaTopics.TICKET_EVENTS,
            {
                "event_type": KafkaEventTypes.TICKET_UPLOADED,
                "pnr": pnr,
                "booking_id": str(booking_id),
                "user_id": str(user_id),
                "user_email": user_email,
            },
        )
