import json

import aio_pika
from aio_pika import Channel, Connection, Exchange
from core.settings import Settings
from queues.base_queue import BaseQueueEmitter


class RabbitMQEmitter(BaseQueueEmitter):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.connection: Connection | None = None
        self.channel: Channel | None = None
        self.exchange: Exchange | None = None

    async def connect(self) -> None:
        """Установить соединение с RabbitMQ"""
        if self.connection is not None:
            return

        self.connection = await aio_pika.connect_robust(
            host=self.settings.rabbitmq_host,
            port=self.settings.rabbitmq_port,
            login=self.settings.rabbitmq_user,
            password=self.settings.rabbitmq_password,
        )
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.get_exchange(
            self.settings.rabbitmq_exchange,
        )

    async def disconnect(self) -> None:
        """Закрыть соединение с RabbitMQ"""
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.channel = None
            self.exchange = None

    async def send_message(self, message: dict, routing_key: str) -> None:
        """Отправить сообщение в очередь"""
        if not self.exchange:
            raise RuntimeError("Connection to RabbitMQ is not established")

        await self.exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )
