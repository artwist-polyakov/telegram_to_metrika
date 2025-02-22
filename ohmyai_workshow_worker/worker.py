import asyncio
import csv
import io
import json
import logging
import re
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import aio_pika
import requests
from aio_pika.abc import AbstractIncomingMessage
from core.settings import get_settings

settings = get_settings()

# Настраиваем логирование
logging.basicConfig(
    level=settings.logging_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/var/log/worker.log"),
    ],
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
        # Словари для хранения сообщений по типам ID
        self.ymclid_messages: Dict[str, List[Tuple[AbstractIncomingMessage, dict]]] = (
            defaultdict(list)
        )
        self.yclid_messages: Dict[str, List[Tuple[AbstractIncomingMessage, dict]]] = (
            defaultdict(list)
        )

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

    def create_csv(self, conversions: List[Tuple[str, int]]) -> str:
        logger.info(f"Создаем CSV файл для {len(conversions)} конверсий")
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ClientId", "Target", "DateTime"])
        for client_id, timestamp in conversions:
            writer.writerow([client_id, CONVERSION_TARGET, timestamp])
        csv_content = output.getvalue()
        logger.debug(f"Подготовлен CSV файл:\n{csv_content}")
        return csv_content

    def upload_to_metrika(self, file_content: str):
        logger.info("Отправляем данные в Яндекс.Метрику...")
        url = f"https://api-metrika.yandex.net/management/v1/counter/{COUNTER_ID}/offline_conversions/upload"  # noqa E501
        headers = {"Authorization": f"OAuth {settings.yandex_metrika_api_key}"}
        response = requests.post(url, headers=headers, files={"file": file_content})
        response.raise_for_status()
        logger.info("Данные успешно загружены в Яндекс.Метрику")
        return response

    async def process_batch(
        self, messages: List[Tuple[AbstractIncomingMessage, dict]], id_type: str
    ):
        if not messages:
            logger.info(f"Нет сообщений для обработки с типом ID: {id_type}")
            return

        conversions = []
        for _, data in messages:
            ymclid, yclid = self.parse_payload(data["payload"])
            client_id = ymclid if id_type == "ymclid" else yclid
            timestamp = data["current_timestamp"]
            if client_id and client_id != "null":
                conversions.append((client_id, timestamp))

        if not conversions:
            logger.info(f"Нет валидных конверсий для {id_type}")
            # Подтверждаем сообщения без валидных конверсий
            for message, _ in messages:
                await message.ack()
            return

        try:
            csv_content = self.create_csv(conversions)
            response = self.upload_to_metrika(csv_content)

            if response.status_code == 200:
                logger.info(f"Успешная загрузка для {id_type}")
                # Подтверждаем все сообщения в пакете
                for message, _ in messages:
                    await message.ack()
            else:
                logger.error(f"Ошибка загрузки для {id_type}: {response.status_code}")
                # Возвращаем сообщения в очередь
                for message, _ in messages:
                    await message.reject(requeue=True)
        except Exception as e:
            logger.error(f"Ошибка при обработке пакета {id_type}: {str(e)}")
            for message, _ in messages:
                await message.reject(requeue=True)

    async def collect_messages(self) -> int:
        messages_processed = 0

        try:
            async with self.queue.iterator(timeout=5) as queue_iter:
                async for message in queue_iter:
                    try:
                        body = message.body.decode()
                        data = json.loads(body)
                        logger.debug(f"Получено сообщение: {body}")

                        if not data.get("payload"):
                            logger.debug("Сообщение без payload, пропускаем")
                            await message.ack()
                            continue

                        ymclid, yclid = self.parse_payload(data["payload"])

                        if ymclid == "null" and yclid == "null":
                            logger.debug("Оба ID null, пропускаем сообщение")
                            await message.ack()
                            continue

                        if ymclid and ymclid != "null":
                            logger.debug(
                                f"Добавляем сообщение в ymclid группу: {ymclid}"
                            )
                            self.ymclid_messages[ymclid].append((message, data))
                        elif yclid and yclid != "null":
                            logger.debug(f"Добавляем сообщение в yclid группу: {yclid}")
                            self.yclid_messages[yclid].append((message, data))
                        else:
                            logger.debug("Нет валидных ID, пропускаем")
                            await message.ack()
                            continue

                        messages_processed += 1

                    except Exception as e:
                        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
                        await message.reject(requeue=True)

        except asyncio.TimeoutError:
            logger.info("Таймаут ожидания сообщений, завершаем сбор.")

        logger.info(
            f"Собрано сообщений: {messages_processed} (ymclid: {len(self.ymclid_messages)}, yclid: {len(self.yclid_messages)})"
        )
        return messages_processed

    async def process_collected_messages(self):
        # Обработка ymclid сообщений
        ymclid_batch = [
            (msg, data)
            for messages in self.ymclid_messages.values()
            for msg, data in messages
        ]
        await self.process_batch(ymclid_batch, "ymclid")

        # Ждем 1 секунду между загрузками файлов
        await asyncio.sleep(1)

        # Обработка yclid сообщений
        yclid_batch = [
            (msg, data)
            for messages in self.yclid_messages.values()
            for msg, data in messages
        ]
        await self.process_batch(yclid_batch, "yclid")

    async def run_once(self):
        try:
            await self.connect()
            processed_count = await self.collect_messages()
            if processed_count > 0:
                await self.process_collected_messages()
            await self.connection.close()
        except Exception as e:
            logger.error(f"Ошибка в процессе выполнения: {str(e)}")
            if self.connection and not self.connection.is_closed:
                await self.connection.close()


async def main():
    logger.info("Запуск обработки сообщений Workshow")
    worker = MetrikaWorker()
    await worker.run_once()


if __name__ == "__main__":
    asyncio.run(main())
