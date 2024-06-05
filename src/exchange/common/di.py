from typing import AsyncIterable

from aio_pika import Exchange
from dishka import Provider, Scope, provide

from exchange.common.broker import get_connection, setup_exchange


class ExchangeProvider(Provider):
    scope = Scope.APP

    def __init__(self, rabbit_url: str, exchange_name: str) -> None:
        super().__init__()
        self._rabbit_url = rabbit_url
        self._exchange_name = exchange_name

    @provide
    async def get_exchange(self) -> AsyncIterable[Exchange]:
        connection = await get_connection(self._rabbit_url)
        channel = await connection.channel()
        exchange = await setup_exchange(self._exchange_name, channel)
        yield exchange
        await connection.close()
