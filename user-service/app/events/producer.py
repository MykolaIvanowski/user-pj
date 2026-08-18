from __future__ import annotations

import json
import logging

from app.core.config import get_settings

logger = logging.getLogger("event-producer")

producer = None


async def get_producer():
    global producer
    if producer is None:
        try:
            from aiokafka import AIOKafkaProducer  # type: ignore

            settings = get_settings()
            logger.info("Starting Kafka producer...")
            producer = AIOKafkaProducer(bootstrap_servers=settings.EVENT_BROKER_URL)
            await producer.start()
            logger.info("Kafka producer started")
        except Exception as exc:  # pragma: no cover
            logger.warning("Kafka producer unavailable: %s", exc)
            return None
    return producer


async def publish_event(topic: str, payload: dict):
    logger.info("Publishing event: %s -> %s", topic, payload)
    try:
        p = await get_producer()
        if p is None:
            logger.info("Event (no broker): %s %s", topic, payload)
            return
        await p.send_and_wait(topic, json.dumps(payload).encode("utf-8"))
    except Exception as exc:  # pragma: no cover
        logger.warning("publish_event failed: %s", exc)
