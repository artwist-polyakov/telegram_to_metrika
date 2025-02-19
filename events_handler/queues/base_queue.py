from abc import ABC, abstractmethod


class BaseQueueEmitter(ABC):
    @abstractmethod
    async def connect(self) -> None:
        """Установить соединение с очередью"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Закрыть соединение с очередью"""
        pass

    @abstractmethod
    async def send_message(self, message: dict, routing_key: str) -> None:
        """Отправить сообщение в очередь"""
        pass
