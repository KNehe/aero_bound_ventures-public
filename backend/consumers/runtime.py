import asyncio

from backend.consumers.booking_notifications import process_booking_notifications
from backend.consumers.payment_notifications import process_payment_notifications
from backend.consumers.ticket_notifications import process_ticket_notifications
from backend.consumers.user_notifications import process_user_notifications
from backend.utils.constants import KAFKA_GROUP_ID, KafkaTopics
from backend.utils.consumer import EventConsumer

NOTIFICATION_HANDLERS = {
    KafkaTopics.USER_EVENTS: process_user_notifications,
    KafkaTopics.BOOKING_EVENTS: process_booking_notifications,
    KafkaTopics.PAYMENT_EVENTS: process_payment_notifications,
    KafkaTopics.TICKET_EVENTS: process_ticket_notifications,
}

notification_consumer = EventConsumer(group_id=KAFKA_GROUP_ID)


def register_notification_handlers(consumer: EventConsumer) -> None:
    for topic, handler in NOTIFICATION_HANDLERS.items():
        consumer.register_handler(topic, handler)


def start_notification_consumer(
    loop: asyncio.AbstractEventLoop, consumer: EventConsumer | None = None
) -> None:
    active_consumer = consumer if consumer is not None else notification_consumer
    register_notification_handlers(active_consumer)
    active_consumer.start(loop)


def stop_notification_consumer(consumer: EventConsumer | None = None) -> None:
    active_consumer = consumer if consumer is not None else notification_consumer
    active_consumer.stop()
