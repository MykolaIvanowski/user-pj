import json
import logging
from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger("event-producer")

producer = None

async def get_producer():
    global producer
    if producer is None:
        logger.info("Starting Kafka producer...")
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.EVENT_BROKER_URL
        )
        await producer.start()
        logger.info("Kafka producer started")
    return producer

async def publish_event(topic: str, payload: dict):
    logger.info(f"Publishing event: {topic} -> {payload}")
    p = await get_producer()
    await p.send_and_wait(topic, json.dumps(payload).encode("utf-8"))
