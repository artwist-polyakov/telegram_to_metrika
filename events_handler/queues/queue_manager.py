from typing import Optional

from core.settings import Settings
from queues.rabbit_queue import RabbitMQEmitter


class QueueManager:
    _instance: Optional["QueueManager"] = None
    _emitter: Optional[RabbitMQEmitter] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, settings: Settings) -> None:
        if cls._emitter is None:
            cls._emitter = RabbitMQEmitter(settings)

    @classmethod
    async def connect(cls) -> None:
        if cls._emitter:
            await cls._emitter.connect()

    @classmethod
    async def disconnect(cls) -> None:
        if cls._emitter:
            await cls._emitter.disconnect()

    @classmethod
    async def send_message(cls, message: dict, routing_key: str) -> None:
        if cls._emitter:
            await cls._emitter.send_message(message, routing_key)
