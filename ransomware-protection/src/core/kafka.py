import asyncio
import json
import logging
from typing import Callable, Optional, Any
from contextlib import asynccontextmanager

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_producer: Optional[KafkaProducer] = None
_consumers: dict[str, KafkaConsumer] = {}


async def init_kafka():
    global _producer
    try:
        _producer = KafkaProducer(
            bootstrap_servers=settings.kafka.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            retries=3,
            max_in_flight_requests_per_connection=1,
        )
        logger.info("Kafka producer initialized successfully")
    except KafkaError as e:
        logger.error(f"Failed to initialize Kafka producer: {e}")
        raise


async def close_kafka():
    global _producer, _consumers
    if _producer:
        _producer.flush()
        _producer.close()
        logger.info("Kafka producer closed")
    for name, consumer in _consumers.items():
        consumer.close()
        logger.info(f"Kafka consumer {name} closed")


async def get_producer() -> KafkaProducer:
    if _producer is None:
        await init_kafka()
    return _producer


async def publish_event(topic: str, key: str, value: dict) -> bool:
    try:
        producer = await get_producer()
        future = producer.send(topic, key=key, value=value)
        await asyncio.to_thread(future.get, timeout=10)
        return True
    except Exception as e:
        logger.error(f"Failed to publish to Kafka topic {topic}: {e}")
        return False


async def publish_alert(alert_data: dict) -> bool:
    return await publish_event(
        settings.kafka.topics["alerts"], key=str(alert_data.get("id", "")), value=alert_data
    )


async def publish_response(response_data: dict) -> bool:
    return await publish_event(
        settings.kafka.topics["responses"],
        key=str(response_data.get("action", "")),
        value=response_data,
    )


class KafkaConsumerManager:
    def __init__(self, name: str):
        self.name = name
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False
        self._task: Optional[asyncio.Task] = None

    async def start(
        self, topics: list[str], handler: Callable[[dict], Any], group_id: Optional[str] = None
    ):
        try:
            self.consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=settings.kafka.bootstrap_servers,
                group_id=group_id or f"{settings.kafka.consumer_group}-{self.name}",
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset=settings.kafka.auto_offset_reset,
                enable_auto_commit=True,
                max_poll_records=500,
            )
            _consumers[self.name] = self.consumer
            self.running = True
            self._task = asyncio.create_task(self._consume(handler))
            logger.info(f"Kafka consumer {self.name} started for topics: {topics}")
        except KafkaError as e:
            logger.error(f"Failed to start Kafka consumer {self.name}: {e}")
            raise

    async def _consume(self, handler: Callable[[dict], Any]):
        try:
            while self.running:
                records = await asyncio.to_thread(self.consumer.poll, timeout_ms=1000)
                for topic_partition, messages in records.items():
                    for message in messages:
                        try:
                            await handler(message.value)
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
        except Exception as e:
            logger.error(f"Consumer {self.name} error: {e}")
        finally:
            logger.info(f"Consumer {self.name} stopped")

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.consumer:
            self.consumer.close()
            if self.name in _consumers:
                del _consumers[self.name]
        logger.info(f"Kafka consumer {self.name} stopped")


def create_consumer_manager(name: str) -> KafkaConsumerManager:
    return KafkaConsumerManager(name)
