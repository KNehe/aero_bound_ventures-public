from typing import Any, Protocol


class KafkaTopicClient(Protocol):
    def list_topics(self, timeout: int) -> Any: ...


class KafkaProducerManager(Protocol):
    producer: KafkaTopicClient


class KafkaProducerHealthProbe:
    service_name = "kafka_producer"

    def __init__(self, producer_manager: KafkaProducerManager):
        self.producer_manager = producer_manager

    def check(self) -> None:
        metadata = self.producer_manager.producer.list_topics(timeout=1)
        if not metadata or not metadata.brokers:
            raise RuntimeError("No brokers reached")
