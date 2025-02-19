from abc import ABC, abstractmethod


class BaseQueueEmitter(ABC):
    @abstractmethod
    async def send_message(self, message: dict):
        pass
