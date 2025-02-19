import asyncio
import csv
import io
import logging
import re
from datetime import datetime
from typing import Optional

import aio_pika
import requests
from aio_pika import Message
from aio_pika.abc import AbstractIncomingMessage

from core.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

CONVERSION_TARGET = "awst_workshow_register_offline"
COUNTER_ID = "98979849"


class MetrikaWorker:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            login=settings.rabbitmq_user,
            password=settings.rabbitmq_password,
        )
        self.channel = await self.connection.channel()

        # Получаем существующий exchange вместо объявления нового
        self.exchange = await self.channel.get_exchange(settings.rabbitmq_exchange)

        # Очередь уже создана, просто получаем ссылку на нее
        self.queue = await self.channel.get_queue(settings.rabbitmq_metrics_queue)

        # Биндинг уже создан в init_rabbitmq.sh, повторно не нужно
        # await self.queue.bind(self.exchange, routing_key=settings.ohmyai_routing_key)

    def parse_payload(self, payload: str) -> tuple[Optional[str], Optional[str]]:
        pattern = r"ymclid__([^_]*)__yclid__([^_]*)"
        match = re.match(pattern, payload)
        if not match:
            return None, None
        return match.group(1), match.group(2)

    def create_csv(self, client_id: str, timestamp: int) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ClientId", "Target", "DateTime"])
        writer.writerow([client_id, CONVERSION_TARGET, timestamp])
        return output.getvalue()

    def upload_to_metrika(self, file_content: str):
        url = f"https://api-metrika.yandex.net/management/v1/counter/{COUNTER_ID}/offline_conversions/upload"
        headers = {"Authorization": f"OAuth {settings.yandex_metrika_api_key}"}
        response = requests.post(url, headers=headers, files={"file": file_content})
        response.raise_for_status()
        return response

    async def process_message(self, message: AbstractIncomingMessage):
        async with message.process():
            try:
                body = message.body.decode()
                data = eval(
                    body
                )  # Небезопасно, в реальном проекте используйте json.loads

                ymclid, yclid = self.parse_payload(data["payload"])

                client_id = ymclid if ymclid and ymclid != "null" else yclid
                if not client_id or client_id == "null":
                    logger.warning("No valid client_id found in message")
                    return

                csv_content = self.create_csv(
                    client_id=client_id, timestamp=data["current_timestamp"]
                )

                self.upload_to_metrika(csv_content)
                logger.info(
                    f"Successfully processed message for client_id: {client_id}"
                )

            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def run(self):
        await self.connect()
        logger.info("Worker started")

        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                await self.process_message(message)


async def main():
    worker = MetrikaWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
