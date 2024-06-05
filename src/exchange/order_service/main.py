import uvicorn
from asgi_monitor.integrations.fastapi import TracingConfig, setup_tracing
from asgi_monitor.logging import configure_logging
from asgi_monitor.logging.uvicorn import build_uvicorn_log_config
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from exchange.common.config import load_config
from exchange.common.di import ExchangeProvider
from exchange.common.telemetry import setup_telemetry
from exchange.order_service.handlers import order_router


def main() -> None:
    config = load_config()
    configure_logging(
        level=config.logging.level,
        json_format=config.logging.json_format,
        include_trace=config.logging.include_trace,
    )

    tracer_provider = setup_telemetry(
        service_name="order",
        otlp_endpoint=config.trace.otlp_endpoint,
    )
    trace_config = TracingConfig(tracer_provider=tracer_provider)
    container = make_async_container(ExchangeProvider(config.rabbit.url, "trades"))

    app = FastAPI()
    app.include_router(order_router)

    setup_dishka(container, app)
    setup_tracing(app, trace_config)

    log_config = build_uvicorn_log_config(
        level=config.logging.level,
        json_format=config.logging.json_format,
        include_trace=config.logging.include_trace,
    )

    uvicorn.run(app, host=config.api.host, port=config.api.port, log_config=log_config)


if __name__ == "__main__":
    main()
