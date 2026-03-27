import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from pydantic import ValidationError

from .config import settings
from .logging_utils import configure_logging, log_kv
from .topics import dlq_topic

producer: AIOKafkaProducer | None = None
consumer_tasks: list[asyncio.Task] = []
logger = configure_logging('shared-kafka')
MAX_RETRIES = 3


async def start_producer():
    global producer
    if producer is None:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
        )
        await producer.start()


async def stop_producer():
    global producer
    if producer is not None:
        await producer.stop()
        producer = None


async def publish(topic: str, value: dict, key: str | None = None):
    if producer is None:
        raise RuntimeError('Kafka producer not started')
    await producer.send_and_wait(topic, value=value, key=key.encode('utf-8') if key else None)


async def publish_dlq(topic: str, value: dict, error: str):
    payload = {**value, 'dlq_error': error}
    log_kv(logger, 'Kafka', 'publish_dlq', topic=dlq_topic(topic), error=error)
    await publish(dlq_topic(topic), payload, key=str(value.get('event_id') or value.get('order_id') or 'dlq'))


async def start_consumer(topic: str | list[str], group_id: str, schema: Any, handler: Callable[[Any], Awaitable[None]]):
    topics = topic if isinstance(topic, list) else [topic]
    consumer = AIOKafkaConsumer(
        *topics,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=group_id,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda b: json.loads(b.decode('utf-8')),
    )
    await consumer.start()

    async def _run():
        try:
            async for msg in consumer:
                raw = msg.value
                source_topic = msg.topic
                try:
                    parsed = schema.model_validate(raw)
                except ValidationError as exc:
                    log_kv(logger, 'Kafka', 'validation_failed', topic=source_topic, error=str(exc))
                    await publish_dlq(source_topic, raw, f'validation_error:{exc}')
                    continue

                retry_count = getattr(parsed, 'retry_count', 0)
                try:
                    await handler(parsed)
                except Exception as exc:
                    if retry_count < MAX_RETRIES:
                        payload = parsed.model_dump(mode='json')
                        payload['retry_count'] = retry_count + 1
                        log_kv(logger, 'Kafka', 'retrying', topic=source_topic, retry=payload['retry_count'], max_retries=MAX_RETRIES, error=str(exc))
                        await publish(source_topic, payload, key=str(payload.get('event_id') or payload.get('order_id')))
                    else:
                        log_kv(logger, 'Kafka', 'dlq_redirect', topic=source_topic, retries=retry_count, error=str(exc))
                        await publish_dlq(source_topic, parsed.model_dump(mode='json'), str(exc))
        finally:
            await consumer.stop()

    task = asyncio.create_task(_run())
    consumer_tasks.append(task)
    return task


async def stop_consumers():
    for task in consumer_tasks:
        task.cancel()
    if consumer_tasks:
        await asyncio.gather(*consumer_tasks, return_exceptions=True)
    consumer_tasks.clear()
