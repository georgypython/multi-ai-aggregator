import asyncio

from src.core.container import container
from src.core.setup import bot, dp, whitelist_guard_ai_service
from src.core.logger import logger


async def main():
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Error while starting bot_polling: {e}")
    finally:
        await dp.storage.close()
        await whitelist_guard_ai_service.aclose()
        await container.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        logger.info(f"Start bot")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(f"Stop bot")
