from abc import ABC, abstractmethod
from typing import Any


class NotificationChannel(ABC):
    @abstractmethod
    async def handle(self, event: Any) -> None: ...

    @abstractmethod
    def can_handle(self, event_type: type) -> bool: ...
