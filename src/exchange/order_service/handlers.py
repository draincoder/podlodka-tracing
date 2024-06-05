import asyncio
import json
import logging
import random
import uuid

from aio_pika import Exchange, Message
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException
from opentelemetry import propagate, trace

from exchange.order_service.models import Order, OrderCreated, Status

order_router = APIRouter(prefix="/orders", tags=["Order"])

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


async def call_market(symbol: str) -> None:
    with tracer.start_as_current_span("check assets", attributes={"symbol": symbol}):
        await asyncio.sleep(random.randint(1, 3) / 10)


@order_router.post("/", response_model=OrderCreated)
@inject
async def create_order(order: Order, exchange: FromDishka[Exchange]) -> OrderCreated:
    logger.info("Received new order %s", order)
    order_attributes = order.model_dump(mode="json")

    with tracer.start_as_current_span("validate order", attributes=order_attributes):
        if order.quantity <= 0:
            raise HTTPException(status_code=422, detail="Invalid quantity")
        await call_market(order.symbol)

    with tracer.start_as_current_span("create order", attributes=order_attributes):
        order_id = uuid.uuid4()
        status = Status.CREATED

    order_attributes["order_id"] = str(order_id)
    order_attributes["status"] = status.value

    with tracer.start_as_current_span("publish to trade", attributes=order_attributes) as span:
        message_body = json.dumps(order_attributes).encode("utf-8")

        headers = {}
        context = trace.set_span_in_context(span)
        propagate.inject(headers, context=context)

        message = Message(body=message_body, headers=headers)
        await exchange.publish(message, routing_key="trade.key")
        span.add_event("order published", {"order_id": str(order_id)})

    return OrderCreated(status=status, order_id=order_id)
