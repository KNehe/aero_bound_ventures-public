import asyncio
import json
import os
import threading
from typing import Callable, Dict
from confluent_kafka import Consumer, KafkaError
from backend.utils.log_manager import get_app_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_app_logger(__name__)


class EventConsumer:
    """
    Unified Kafka Consumer that subscribes to multiple topics and dispatches
    events to registered handlers. Runs in a single background thread.
    """

    def __init__(self, group_id: str):
        self.group_id = group_id
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
        self.handlers: Dict[str, Callable] = {}
        self.consumer = None
        self.running = False
        self.thread = None
        self.loop = None

    def register_handler(self, topic: str, handler: Callable):
        """Register an async handler for a specific topic."""
        self.handlers[topic] = handler
        logger.info(f"Registered handler for topic: {topic}")

    def start(self, loop: asyncio.AbstractEventLoop):
        """Start the consumer thread."""
        if self.running or not self.handlers:
            return

        self.loop = loop
        topics = list(self.handlers.keys())

        conf = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "auto.offset.reset": "earliest",
        }

        try:
            self.consumer = Consumer(conf)
            self.consumer.subscribe(topics)
            self.running = True

            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.info(f"Unified EventConsumer started for topics: {topics}")
        except Exception as e:
            logger.error(f"Failed to start Unified EventConsumer: {e}")

    def stop(self):
        """Stop the consumer thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)

        if self.consumer:
            self.consumer.close()
            logger.info("Unified EventConsumer stopped")

    def _run(self):
        """Polling loop running in a background thread."""
        while self.running:
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    logger.error(f"Consumer error: {msg.error()}")
                continue

            topic = msg.topic()
            handler = self.handlers.get(topic)
            if not handler:
                continue

            try:
                data = json.loads(msg.value().decode("utf-8"))

                # Dispatch to main event loop safely
                if self.loop and not self.loop.is_closed():
                    future = asyncio.run_coroutine_threadsafe(handler(data), self.loop)
                    # Optional: wait for result with timeout to prevent lag spikes
                    future.result(timeout=5)
            except Exception as e:
                logger.error(f"Error processing message from {topic}: {e}")
