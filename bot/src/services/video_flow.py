from uuid import UUID

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types.input_file import BufferedInputFile
import httpx

from src.core.logger import logger
from src.core.schemas import GenerationStatus, VideoGenerationResult
from src.services.video_generation import VideoGenerationService
from src.states import AIFlow


class VideoGenerationFlowService:
    def __init__(
        self,
        video_generation_service: VideoGenerationService,
    ) -> None:
        self.video_generation_service = video_generation_service

    async def process_video_prompt(
        self,
        message: Message,
        state: FSMContext,
        model_id: UUID,
        duration_seconds: int,
        prompt: str,
    ) -> None:
        if message.from_user is None:
            await message.answer(
                "Не удалось определить пользователя. Попробуй еще раз."
            )
            return

        tg_user_id = message.from_user.id
        await message.answer("Принял запрос ✨ Запускаю генерацию видео...")

        generation_result = await self._start_generation(
            message=message,
            tg_user_id=tg_user_id,
            model_id=model_id,
            duration_seconds=duration_seconds,
            prompt=prompt,
        )
        if generation_result is None:
            return

        await message.answer("Генерация запущена ⏳ Обычно это занимает до пары минут.")

        final_status = await self._wait_final_status(
            message=message,
            tg_user_id=tg_user_id,
            generation_id=generation_result.generation_id,
        )
        if final_status is None:
            return

        if not await self._handle_terminal_status(
            message=message, final_status=final_status
        ):
            return

        await message.answer(
            "<b>Готово ✅</b>\n"
            f"Списано: <b>{final_status.tokens_cost:.4f} токенов</b>\n"
            "Отправляю видео..."
        )

        await self._send_generated_video(
            message=message,
            state=state,
            tg_user_id=tg_user_id,
            final_status=final_status,
        )

        await state.set_state(AIFlow.choosing_model)

    async def _start_generation(
        self,
        message: Message,
        tg_user_id: int,
        model_id: UUID,
        duration_seconds: int,
        prompt: str,
    ) -> VideoGenerationResult | None:
        try:
            return await self.video_generation_service.generate_video(
                tg_user_id=tg_user_id,
                model_id=model_id,
                prompt=prompt,
                duration_seconds=duration_seconds,
            )
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code == 402:
                await message.answer("Недостаточно токенов для этой генерации 💸")
            elif status_code == 401:
                await message.answer(
                    "Сервис сейчас временно недоступен. Попробуй чуть позже."
                )
            else:
                await message.answer(
                    "Не удалось запустить генерацию видео. Попробуй чуть позже."
                )
            return None
        except Exception:
            logger.exception("Failed to generate video")
            await message.answer("Ошибка генерации видео. Попробуй позже.")
            return None

    async def _wait_final_status(
        self,
        message: Message,
        tg_user_id: int,
        generation_id: UUID,
    ) -> VideoGenerationResult | None:
        try:
            return await self.video_generation_service.wait_for_video_generation_status(
                tg_user_id=tg_user_id,
                generation_id=generation_id,
            )
        except httpx.HTTPStatusError:
            logger.exception("Backend failed while polling video generation status")
            await message.answer(
                "Не удалось проверить прогресс генерации. Попробуй немного позже."
            )
            return None
        except TimeoutError:
            await message.answer(
                "Генерация заняла слишком много времени. Попробуй еще раз чуть позже ⏱️"
            )
            return None
        except Exception:
            logger.exception("Failed while polling video generation status")
            await message.answer(
                "Не удалось проверить прогресс генерации. Попробуй позже."
            )
            return None

    async def _handle_terminal_status(
        self,
        message: Message,
        final_status: VideoGenerationResult,
    ) -> bool:
        if final_status.status == GenerationStatus.FAILED:
            await message.answer(
                "Не удалось завершить генерацию видео ❌ Попробуй другой запрос."
            )
            return False

        if final_status.status == GenerationStatus.CANCELED:
            await message.answer("Генерация была отменена ❌")
            return False

        if final_status.status != GenerationStatus.COMPLETED:
            await message.answer("Видео еще готовится. Проверь чуть позже ⏳")
            return False

        return True

    async def _send_generated_video(
        self,
        message: Message,
        state: FSMContext,
        tg_user_id: int,
        final_status: VideoGenerationResult,
    ) -> None:
        video_bytes: bytes | None = None
        try:
            video_bytes = (
                await self.video_generation_service.get_video_generation_content(
                    tg_user_id=tg_user_id,
                    generation_id=final_status.generation_id,
                )
            )

            await message.answer_video(
                video=BufferedInputFile(
                    file=video_bytes,
                    filename=f"video_{final_status.generation_id}.mp4",
                ),
                caption=(
                    "<b>Видео готово ✅</b>\n"
                    f"Списано: <b>{final_status.tokens_cost:.4f} токенов</b>"
                ),
            )
        except TelegramBadRequest:
            if video_bytes is None:
                logger.exception(
                    "Telegram failed to process video and no bytes available for fallback"
                )
                await message.answer("Не удалось отправить видео. Попробуй позже.")
                await state.set_state(AIFlow.choosing_model)
                return

            logger.exception("Telegram failed to process video as video")
            await message.answer_document(
                document=BufferedInputFile(
                    file=video_bytes,
                    filename=f"video_{final_status.generation_id}.mp4",
                ),
                caption=(
                    "<b>Видео готово ✅</b>\n"
                    f"Списано: <b>{final_status.tokens_cost:.4f} токенов</b>"
                ),
            )
        except httpx.HTTPStatusError:
            logger.exception("Backend failed to return generated video content")
            await message.answer("Не удалось получить готовое видео. Попробуй позже.")
        except Exception:
            logger.exception("Failed to download/send generated video")
            await message.answer("Не удалось отправить видео. Попробуй позже.")
