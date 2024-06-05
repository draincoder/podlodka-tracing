import asyncio
import logging

from asgi_monitor.logging import configure_logging
from faststream import FastStream
from faststream.rabbit import RabbitBroker
from faststream.rabbit.opentelemetry import RabbitTelemetryMiddleware

from exchange.common.config import load_config
from exchange.common.telemetry import setup_telemetry
from exchange.notification_service.handlers import router

logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config()
    configure_logging(
        level=config.logging.level,
        json_format=config.logging.json_format,
        include_trace=config.logging.include_trace,
    )
    tracer_provider = setup_telemetry(
        service_name="notification",
        otlp_endpoint=config.trace.otlp_endpoint,
    )
    telemetry_middleware = RabbitTelemetryMiddleware(tracer_provider=tracer_provider)
    broker = RabbitBroker(url=config.rabbit.url, middlewares=(telemetry_middleware,))
    broker.include_router(router)
    app = FastStream(broker, logger=logger)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
