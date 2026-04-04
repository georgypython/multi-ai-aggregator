from typing import Any, Awaitable, Callable

import httpx
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.core.logger import logger
from src.services.ai import AIService


class WhitelistGuardMiddleware(BaseMiddleware):
    def __init__(
        self,
        ai_service: AIService,
    ) -> None:
        self._ai_service = ai_service

    async def _is_allowed(self, tg_user_id: int) -> bool:
        allowed = False
        try:
            await self._ai_service.get_user_balance(tg_user_id=tg_user_id)
            allowed = True
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 403:
                logger.warning(
                    "whitelist_guard_backend_error status=%s tg_user_id=%s",
                    exc.response.status_code,
                    tg_user_id,
                )
        except Exception:
            logger.exception(
                "whitelist_guard_unexpected_error tg_user_id=%s", tg_user_id
            )
        return allowed

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user_id: int | None = None

        if isinstance(event, Message) and event.from_user:
            tg_user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            tg_user_id = event.from_user.id

        if tg_user_id is None:
            return await handler(event, data)

        if not await self._is_allowed(tg_user_id):
            return None

        return await handler(event, data)
