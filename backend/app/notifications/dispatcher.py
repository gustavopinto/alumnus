import asyncio
import logging
from functools import wraps
from typing import Any, Callable

from .channels.base import NotificationChannel

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    def __init__(self) -> None:
        self._channels: list[NotificationChannel] = []

    def register(self, channel: NotificationChannel) -> None:
        self._channels.append(channel)

    async def dispatch(self, event: Any) -> None:
        tasks = [ch.handle(event) for ch in self._channels if ch.can_handle(type(event))]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


dispatcher = NotificationDispatcher()


def notifies(extractor: Callable[[Any, dict], Any]):
    """
    Decorator para route handlers async do FastAPI.
    Após o handler retornar com sucesso, chama extractor(result, kwargs) para construir
    um evento de notificação e o despacha em background via asyncio.create_task.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            try:
                event = extractor(result, kwargs)
                if event is not None:
                    task = asyncio.create_task(dispatcher.dispatch(event))
                    task.add_done_callback(_handle_notification_error)
            except Exception:
                logger.exception("Erro ao despachar notificação")
            return result
        return wrapper
    return decorator


def _handle_notification_error(task):
    """Callback para capturar erros em tasks de notificação."""
    try:
        task.result()
    except Exception:
        logger.exception("Erro em task de notificação de background")
