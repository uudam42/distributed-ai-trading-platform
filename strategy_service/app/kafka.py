import json

from aiokafka import AIOKafkaProducer

from .config import settings
from .logging_utils import configure_logging, log_kv

producer: AIOKafkaProducer | None = None
logger = configure_logging('strategy-kafka')


async def start_producer():
    global producer
    if producer is None:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
        )
        await producer.start()
        log_kv(logger, 'StrategyKafka', 'producer_started', bootstrap=settings.kafka_bootstrap_servers)


async def stop_producer():
    global producer
    if producer is not None:
        await producer.stop()
        producer = None
        log_kv(logger, 'StrategyKafka', 'producer_stopped')


async def publish(topic: str, value: dict, key: str | None = None):
    if producer is None:
        raise RuntimeError('Kafka producer not started')
    await producer.send_and_wait(topic, value=value, key=key.encode('utf-8') if key else None)
    log_kv(logger, 'StrategyKafka', 'published', topic=topic, key=key or '')
