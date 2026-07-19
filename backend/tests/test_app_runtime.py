import asyncio
from unittest.mock import call

import pytest
from sqlmodel import SQLModel

from backend import main as backend_main
from backend import worker
from backend.consumers import runtime as notification_runtime
from backend.utils.constants import KafkaTopics


def test_register_notification_handlers(mocker):
    consumer = mocker.Mock()

    notification_runtime.register_notification_handlers(consumer)

    assert consumer.register_handler.call_args_list == [
        call(
            KafkaTopics.USER_EVENTS,
            notification_runtime.process_user_notifications,
        ),
        call(
            KafkaTopics.BOOKING_EVENTS,
            notification_runtime.process_booking_notifications,
        ),
        call(
            KafkaTopics.PAYMENT_EVENTS,
            notification_runtime.process_payment_notifications,
        ),
        call(
            KafkaTopics.TICKET_EVENTS,
            notification_runtime.process_ticket_notifications,
        ),
    ]


@pytest.mark.asyncio
async def test_api_lifespan_manages_producer_without_creating_schema(mocker):
    create_all = mocker.patch.object(SQLModel.metadata, "create_all")
    producer_start = mocker.patch.object(backend_main.kafka_producer, "start")
    producer_stop = mocker.patch.object(backend_main.kafka_producer, "stop")
    consumer_start = mocker.patch.object(
        notification_runtime, "start_notification_consumer"
    )
    consumer_stop = mocker.patch.object(
        notification_runtime, "stop_notification_consumer"
    )

    async with backend_main.lifespan(backend_main.app):
        pass

    create_all.assert_not_called()
    producer_start.assert_called_once_with()
    producer_stop.assert_called_once_with()
    consumer_start.assert_not_called()
    consumer_stop.assert_not_called()


@pytest.mark.asyncio
async def test_worker_starts_and_stops_notification_consumer(mocker):
    shutdown_event = asyncio.Event()
    shutdown_event.set()
    consumer_start = mocker.patch.object(worker, "start_notification_consumer")
    consumer_stop = mocker.patch.object(worker, "stop_notification_consumer")
    producer_start = mocker.patch.object(backend_main.kafka_producer, "start")

    await worker.run_worker(shutdown_event)

    consumer_start.assert_called_once()
    assert isinstance(consumer_start.call_args.args[0], asyncio.AbstractEventLoop)
    consumer_stop.assert_called_once_with()
    producer_start.assert_not_called()
