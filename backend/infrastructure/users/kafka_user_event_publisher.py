from uuid import UUID

from backend.utils.constants import KafkaEventTypes, KafkaTopics
from backend.utils.kafka import KafkaProducer


class KafkaUserEventPublisher:
    def __init__(self, producer: KafkaProducer):
        self.producer = producer

    def publish_user_registered(self, *, user_id: UUID, email: str) -> None:
        self.producer.send(
            KafkaTopics.USER_EVENTS,
            {
                "event_type": KafkaEventTypes.USER_REGISTERED,
                "email": email,
                "user_id": str(user_id),
            },
        )

    def publish_password_reset_requested(self, *, email: str, reset_token: str) -> None:
        self.producer.send(
            KafkaTopics.USER_EVENTS,
            {
                "event_type": KafkaEventTypes.PASSWORD_RESET_REQUESTED,
                "email": email,
                "reset_token": reset_token,
            },
        )

    def publish_password_changed(self, *, user_id: UUID, email: str) -> None:
        self.producer.send(
            KafkaTopics.USER_EVENTS,
            {
                "event_type": KafkaEventTypes.PASSWORD_CHANGED,
                "email": email,
                "user_id": str(user_id),
            },
        )
