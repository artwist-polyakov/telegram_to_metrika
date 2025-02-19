from abc import ABC, abstractmethod


class QueueService(ABC):
    """Базовый интерфейс для сервиса работы с очередью"""

    @abstractmethod
    async def send_to_queue(self, message: dict, routing_key: str) -> None:
        """Отправить сообщение в очередь"""
        pass
