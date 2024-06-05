import uuid
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class Direction(Enum):
    BUY = "BUY"
    SELL = "SELL"


class Status(Enum):
    CREATED = "CREATED"
    CANCELED = "CANCELED"


class Order(BaseModel):
    symbol: str
    quantity: int
    type: Direction


class OrderCreated(BaseModel):
    order_id: UUID = Field(default_factory=lambda: uuid.uuid4())
    status: Status
