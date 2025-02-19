import logging
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    logging_level: int = logging.INFO
    yandex_metrika_api_key: str
    project_port: int
    project_name: str = "Events handler"

    # RabbitMQ settings
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str
    rabbitmq_password: str
    rabbitmq_exchange: str = "metrika_exchange"
    rabbitmq_metrics_queue: str = "metrics_queue"
    ohmyai_routing_key: str = "metrics.ohmyai"


@lru_cache
def get_settings() -> Settings:
    return Settings()
