from functools import lru_cache

from core.settings import get_settings
from queues.queue_manager import QueueManager
from service.base_queue_service import QueueService


class QueueServiceImpl(QueueService):
    """Реализация сервиса для работы с очередью"""

    async def send_to_queue(self, message: dict, routing_key: str) -> None:
        await QueueManager.send_message(message=message, routing_key=routing_key)


@lru_cache
def get_queue_service() -> QueueService:
    """Получить инстанс сервиса для работы с очередью"""
    return QueueServiceImpl()
