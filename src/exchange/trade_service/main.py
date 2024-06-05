import asyncio
import logging

from aio_pika import ExchangeType, connect_robust
from asgi_monitor.logging import configure_logging

from exchange.common.config import load_config
from exchange.common.telemetry import setup_telemetry
from exchange.trade_service.handlers import handle_trade

logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config()
    configure_logging(
        level=config.logging.level,
        json_format=config.logging.json_format,
        include_trace=config.logging.include_trace,
    )
    setup_telemetry(
        service_name="trade",
        otlp_endpoint=config.trace.otlp_endpoint,
    )

    connection = await connect_robust(config.rabbit.url)
    channel = await connection.channel()

    source_exchange = await channel.declare_exchange("trades", ExchangeType.TOPIC)
    dest_exchange = await channel.declare_exchange("notifications", ExchangeType.TOPIC)

    queue = await channel.declare_queue(exclusive=True)
    await queue.bind(source_exchange, "trade.key")
    dest_queue = await channel.declare_queue(name="notifications")
    await dest_queue.bind(dest_exchange, "notifications.key")

    logger.info("Trade service started")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                try:
                    await handle_trade(message, dest_exchange)
                except Exception as e:
                    logger.exception(e)  # noqa: TRY401


if __name__ == "__main__":
    asyncio.run(main())
