from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from dishka.integrations.aiogram import setup_dishka

from .container import container
from .config import settings
from src.handlers import router
from src.middlewares.whitelist_guard import WhitelistGuardMiddleware
from src.services.ai import AIService

whitelist_guard_ai_service = AIService(
    base_url=settings.ai.ai_api_url,
    api_key=settings.ai.api_key,
    timeout_seconds=settings.ai.request_timeout_seconds,
)


def setup_bot() -> Bot:
    if settings.tg.bot_token:
        return Bot(
            token=settings.tg.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    else:
        raise ValueError("Bot token is None!")


def setup_dispatcher() -> Dispatcher:
    storage = RedisStorage.from_url(settings.redis.url)
    dp = Dispatcher(storage=storage)
    dp.update.middleware(
        WhitelistGuardMiddleware(ai_service=whitelist_guard_ai_service)
    )
    dp.include_router(router)
    setup_dishka(container=container, router=dp, auto_inject=True)
    return dp


bot = setup_bot()
dp = setup_dispatcher()
