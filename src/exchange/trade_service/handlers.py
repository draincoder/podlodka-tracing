import asyncio
import json
import logging
import random
from decimal import Decimal

from aio_pika import Exchange, Message
from opentelemetry import propagate, trace
from opentelemetry.semconv.trace import SpanAttributes

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


async def get_index_price(symbol: str) -> Decimal:
    if symbol == "BTC":
        raise ValueError("BTC not supported")

    with tracer.start_as_current_span("get_index_price", attributes={"symbol": symbol}):
        await asyncio.sleep(random.randint(1, 3) / 10)
        return Decimal(random.randint(1000, 1500))


async def handle_trade(message: Message, dest_exchange: Exchange) -> None:
    logger.info("Received a new trade")

    remote_context = propagate.extract(message.headers)

    msg_attributes = {
        SpanAttributes.MESSAGING_MESSAGE_PAYLOAD_SIZE_BYTES: message.body_size or 0,
        SpanAttributes.MESSAGING_MESSAGE_CONVERSATION_ID: message.correlation_id or "",
    }

    with tracer.start_as_current_span(
        "trades create",
        context=remote_context,
        attributes=msg_attributes,
        end_on_exit=False,
    ) as root:
        trade_data = json.loads(message.body)

    process_context = trace.set_span_in_context(span=root)

    with tracer.start_as_current_span("trades process", context=process_context, attributes=msg_attributes):
        trade_data["status"] = "PENDING"
        price = await get_index_price(trade_data["symbol"])
        trade_data["price"] = str(price)
        trade_data["status"] = "CLOSED"

        with tracer.start_as_current_span("notifications publish", attributes=msg_attributes) as span:
            headers = {}
            context = trace.set_span_in_context(span)
            propagate.inject(headers, context=context)

            message_body = json.dumps(trade_data).encode("utf-8")
            message = Message(body=message_body, headers=headers)
            await dest_exchange.publish(message, routing_key="notifications.key")
            span.add_event("notification published", {"order_id": trade_data["order_id"]})

    root.end()

    logger.info("Trade processed successfully")
