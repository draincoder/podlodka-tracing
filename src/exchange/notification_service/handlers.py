import asyncio
import logging
import random
from typing import Any

from faststream.rabbit import RabbitQueue, RabbitRouter
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
router = RabbitRouter()


async def send_notification(text: str) -> None:
    with tracer.start_as_current_span("send notification", attributes={"text": text}):
        sleep = random.randint(1, 5) / 10
        await asyncio.sleep(sleep)

    logger.info("Notification sent successfully")


@router.subscriber(RabbitQueue(name="notifications", routing_key="notifications.key"))
async def notifications_handler(message: dict[str, Any]) -> None:
    logging.info("Received message [%s]", message)
    await send_notification(message["status"])
