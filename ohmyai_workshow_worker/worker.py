import asyncio
import csv
import io
import logging
import re
from typing import Optional

import aio_pika
import requests
from aio_pika.abc import AbstractIncomingMessage
from core.settings import get_settings

settings = get_settings()

# Настраиваем логирование
logging.basicConfig(
    level=settings.logging_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
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
        logger.info("Подключаемся к RabbitMQ...")
        self.connection = await aio_pika.connect_robust(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            login=settings.rabbitmq_user,
            password=settings.rabbitmq_password,
        )
        self.channel = await self.connection.channel()
        logger.info("Подключение к RabbitMQ установлено")

        logger.info(f"Получаем exchange '{settings.rabbitmq_exchange}'")
        self.exchange = await self.channel.get_exchange(settings.rabbitmq_exchange)

        logger.info(f"Получаем очередь '{settings.rabbitmq_metrics_queue}'")
        self.queue = await self.channel.get_queue(settings.rabbitmq_metrics_queue)

    def parse_payload(self, payload: str) -> tuple[Optional[str], Optional[str]]:
        logger.debug(f"Парсим payload: {payload}")
        pattern = r"ymclid__([^_]*)__yclid__([^_]*)"
        match = re.match(pattern, payload)
        if not match:
            logger.warning(f"Не удалось распарсить payload: {payload}")
            return None, None
        ymclid, yclid = match.group(1), match.group(2)
        logger.info(f"Получены ID: ymclid={ymclid}, yclid={yclid}")
        return ymclid, yclid

    def create_csv(self, client_id: str, timestamp: int) -> str:
        logger.info(
            f"Создаем CSV файл для client_id={client_id}, timestamp={timestamp}"
        )
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ClientId", "Target", "DateTime"])
        writer.writerow([client_id, CONVERSION_TARGET, timestamp])
        csv_content = output.getvalue()
        logger.debug(f"Подготовлен CSV файл:\n{csv_content}")
        return csv_content

    def upload_to_metrika(self, file_content: str):
        logger.info("Отправляем данные в Яндекс.Метрику...")
        url = f"https://api-metrika.yandex.net/management/v1/counter/{COUNTER_ID}/offline_conversions/upload" # noqa E501
        headers = {"Authorization": f"OAuth {settings.yandex_metrika_api_key}"}
        response = requests.post(url, headers=headers, files={"file": file_content})
        response.raise_for_status()
        logger.info("Данные успешно загружены в Яндекс.Метрику")
        return response

    async def process_message(self, message: AbstractIncomingMessage):
        async with message.process():
            try:
                logger.info("Получено новое сообщение")
                body = message.body.decode()
                logger.debug(f"Содержимое сообщения: {body}")

                data = eval(
                    body
                )  # Небезопасно, в реальном проекте используйте json.loads
                logger.info(
                    f"Обрабатываем сообщение для пользователя: {data.get('username')}"
                )

                ymclid, yclid = self.parse_payload(data["payload"])

                client_id = ymclid if ymclid and ymclid != "null" else yclid
                if not client_id or client_id == "null":
                    logger.warning("Не найден валидный client_id в сообщении")
                    return

                logger.info(f"Используем client_id: {client_id}")
                csv_content = self.create_csv(
                    client_id=client_id, timestamp=data["current_timestamp"]
                )

                self.upload_to_metrika(csv_content)
                logger.info(f"Сообщение успешно обработано для client_id: {client_id}")

            except Exception as e:
                logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)

    async def run(self):
        await self.connect()
        logger.info("Воркер запущен и готов к обработке сообщений")

        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                await self.process_message(message)


async def main():
    logger.info("Запуск воркера для обработки сообщений Workshow")
    worker = MetrikaWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
