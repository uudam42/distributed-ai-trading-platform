import asyncio
import json

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from .config import settings
from .logging_utils import configure_logging, log_kv

producer: AIOKafkaProducer | None = None
consumer_task: asyncio.Task | None = None
logger = configure_logging('ai-copilot-kafka')


async def start_producer():
    global producer
    if producer is None:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
        )
        await producer.start()
        log_kv(logger, 'AICopilotKafka', 'producer_started', bootstrap=settings.kafka_bootstrap_servers)


async def stop_producer():
    global producer
    if producer is not None:
        await producer.stop()
        producer = None
        log_kv(logger, 'AICopilotKafka', 'producer_stopped')


async def publish(topic: str, value: dict, key: str | None = None):
    if producer is None:
        raise RuntimeError('Kafka producer not started')
    await producer.send_and_wait(topic, value=value, key=key.encode('utf-8') if key else None)
    log_kv(logger, 'AICopilotKafka', 'published', topic=topic, key=key or '')


async def start_consumer(handler):
    global consumer_task
    consumer = AIOKafkaConsumer(
        'ai.analysis.request.v1',
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id='ai-copilot-service',
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda b: json.loads(b.decode('utf-8')),
    )
    await consumer.start()

    async def _run():
        try:
            async for msg in consumer:
                await handler(msg.value)
        finally:
            await consumer.stop()

    consumer_task = asyncio.create_task(_run())


async def stop_consumer():
    global consumer_task
    if consumer_task:
        consumer_task.cancel()
        await asyncio.gather(consumer_task, return_exceptions=True)
        consumer_task = None
