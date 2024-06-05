from aio_pika import Channel, connect_robust
from aio_pika.abc import AbstractExchange, AbstractRobustConnection, ExchangeType


async def get_connection(rabbit_url: str) -> AbstractRobustConnection:
    return await connect_robust(rabbit_url)


async def setup_exchange(exchange_name: str, channel: Channel) -> AbstractExchange:
    return await channel.declare_exchange(exchange_name, ExchangeType.TOPIC)
