from uuid import UUID

from aiogram import Bot

from src.services import NotificationsService, WaveSpeedService
from src.models.enums import GenerationStatus, GenerationType

from src.core.config import settings


async def delivery_generation_result(
    status: GenerationStatus,
    result_url: str,
    user_telegram_id: int,
    wavespeed: WaveSpeedService,
    generation_type: GenerationType,
    generation_id: UUID,
) -> None:
    bot = Bot(token=settings.tg.bot_token)
    notification = NotificationsService(bot=bot)
    if status == GenerationStatus.COMPLETED:
        generation_bytes = await wavespeed.download_generation_bytes(url=result_url)
        await notification.send_media_generation_success_message(
            media=generation_bytes,
            telegram_user_id=user_telegram_id,
            generation_type=generation_type,
            generation_id=generation_id,
        )
    else:
        await notification.send_generation_failed_message(
            telegram_user_id=user_telegram_id
        )
    await bot.close()
