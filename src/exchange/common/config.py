import os
import tomllib
from dataclasses import dataclass
from typing import Any

from adaptix import Retort

DEFAULT_CONFIG_PATH = "./config/config.toml"


@dataclass
class RabbitConfig:
    user: str
    password: str
    port: int = 5672
    host: str = "localhost"

    @property
    def url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"


@dataclass
class LoggingConfig:
    level: str | int
    json_format: bool = False
    include_trace: bool = False


@dataclass
class TraceConfig:
    otlp_endpoint: str


@dataclass
class ApiConfig:
    host: str = "127.0.0.1"
    port: int = 8080


@dataclass
class Config:
    logging: LoggingConfig
    rabbit: RabbitConfig
    api: ApiConfig
    trace: TraceConfig


def read_toml(path: str) -> dict[str, Any]:
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config() -> Config:
    path = os.getenv("CONFIG_PATH", DEFAULT_CONFIG_PATH)
    data = read_toml(path)
    mapper = Retort()
    return mapper.load(data, Config)
