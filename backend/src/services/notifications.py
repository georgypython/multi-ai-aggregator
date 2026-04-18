from uuid import UUID

from aiogram import Bot
from aiogram.types.input_file import BufferedInputFile

from src.models.enums import GenerationType


class NotificationsService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send_media_generation_success_message(
        self,
        media: bytes,
        telegram_user_id: int,
        generation_id: UUID,
        generation_type: GenerationType,
    ) -> None:
        if generation_type == GenerationType.VIDEO:
            ext = "mp4"
        else:
            ext = "png"

        await self.bot.send_document(
            chat_id=telegram_user_id,
            document=BufferedInputFile(file=media, filename=f"{generation_id}.{ext}"),
            caption="Генерация завершена ✅",
        )

    async def send_generation_failed_message(self, telegram_user_id: int) -> None:
        await self.bot.send_message(
            chat_id=telegram_user_id,
            text="Не удалось завершить генерацию ❌ Попробуйте еще раз позже или напишите в поддержку.",
        )
