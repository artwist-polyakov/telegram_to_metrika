import logging
import os.path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    logging_level: int = logging.INFO
    yandex_metrika_api_key: str = ...
    project_port: int = ...
    project_name: str = "Events handler"

    # RabbitMQ settings
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_exchange: str = "metrika_exchange"
    rabbitmq_metrics_queue: str = "metrics_queue"
    rabbitmq_metrics_routing_key: str = "metrics"

    model_config = SettingsConfigDict(
        env_file=".env" if os.path.exists(".env") else "../.env", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
