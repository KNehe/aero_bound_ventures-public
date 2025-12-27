import os
from confluent_kafka import Producer
from backend.utils.log_manager import get_app_logger
from typing import Any
import json


logger = get_app_logger(__name__)


class KafkaProducer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KafkaProducer, cls).__new__(cls)
            cls._instance.producer = None
            cls._instance.bootstrap_servers = os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"
            )
        return cls._instance

    def start(self):
        if self.producer:
            return
        conf = {
            "bootstrap.servers": self.bootstrap_servers,
            "client.id": "fastapi-producer",
        }
        try:
            self.producer = Producer(conf)
            logger.info(f"Kafka producer started on {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            self.producer = None

    def stop(self):
        if self.producer:
            left = self.producer.flush(timeout=5.0)
            logger.info(f"Kafka producer stopped, {left} messages were not delivered")
            self.producer = None

    def _delivery_report(self, err, msg):
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def send(self, topic: str, message: dict[str, Any]):
        if not self.producer:
            logger.warning(
                f"Kafka producer is not initialized. Message to {topic} skipped."
            )
            return
        try:
            value = json.dumps(message).encode("utf-8")
            self.producer.produce(
                topic=topic, value=value, callback=self._delivery_report
            )
            self.producer.poll(0)
        except Exception as e:
            logger.error(f"Failed to send message to {topic}: {e}")


kafka_producer = KafkaProducer()
