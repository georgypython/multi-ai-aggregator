from html import escape
from uuid import UUID

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types.input_file import BufferedInputFile
from dishka.integrations.aiogram import FromDishka
import httpx

from src.core.logger import logger
from src.keyboards.ai import build_video_sizes_keyboard
from src.services.ai import AIService
from src.services.video_generation import VideoGenerationService
from src.states import AIFlow

router = Router()


@router.callback_query(F.data.startswith("video_duration:"))
async def choose_video_duration(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if callback.message is None:
        await callback.answer("Сообщение не найдено", show_alert=False)
        return

    fsm_data = await state.get_data()
    selected_model_type = fsm_data.get("selected_model_type")
    if selected_model_type != "video":
        await callback.answer("Это не video flow", show_alert=False)
        return

    durations_seconds: list[int] = fsm_data.get("selected_video_durations_seconds", [])
    if not durations_seconds:
        await callback.answer("Сначала выбери video-модель", show_alert=False)
        return

    duration_raw = (
        (callback.data or "").split(":", maxsplit=1)[1] if callback.data else None
    )
    if not duration_raw:
        await callback.answer("Длительность не распознана", show_alert=False)
        return

    try:
        duration_seconds = int(duration_raw)
    except ValueError:
        await callback.answer("Некорректная длительность", show_alert=False)
        return

    if duration_seconds not in durations_seconds:
        await callback.answer("Недоступная длительность", show_alert=False)
        return

    await state.update_data(selected_video_duration_seconds=duration_seconds)
    await state.set_state(AIFlow.choosing_video_size)

    sizes: list[str] = fsm_data.get("selected_video_sizes", [])
    if not sizes:
        await callback.answer("Не найдены размеры для модели", show_alert=True)
        return

    await callback.message.edit_text(
        f"Длительность: <b>{duration_seconds}s</b>\nВыбери размер:",
        reply_markup=build_video_sizes_keyboard(sizes),
    )
    await callback.answer("Длительность выбрана", show_alert=False)


@router.callback_query(F.data.startswith("video_size:"))
async def choose_video_size(
    callback: CallbackQuery,
    ai_service: FromDishka[AIService],
    state: FSMContext,
) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer("Не удалось определить пользователя", show_alert=True)
        return

    fsm_data = await state.get_data()
    selected_model_id = fsm_data.get("selected_model_id")
    selected_model_type = fsm_data.get("selected_model_type")
    selected_duration_seconds = fsm_data.get("selected_video_duration_seconds")

    if selected_model_type != "video" or not selected_model_id:
        await callback.answer("Сначала выбери video-модель", show_alert=False)
        return
    if not selected_duration_seconds:
        await callback.answer("Сначала выбери длительность", show_alert=False)
        return

    size = (callback.data or "").split(":", maxsplit=1)[1] if callback.data else None
    if not size:
        await callback.answer("Размер не распознан", show_alert=False)
        return

    try:
        price_info = await ai_service.get_video_model_price(
            tg_user_id=callback.from_user.id,
            model_id=UUID(selected_model_id),
            duration_seconds=int(selected_duration_seconds),
            size=size,
        )
    except httpx.HTTPStatusError as exc:
        await callback.answer(
            f"Ошибка цены: HTTP {exc.response.status_code}",
            show_alert=True,
        )
        return
    except Exception:
        logger.exception("Failed to get video model price")
        await callback.answer("Ошибка при расчете цены", show_alert=True)
        return

    await state.update_data(
        selected_video_size=size,
        selected_video_tokens_price=price_info.tokens_price,
    )
    await state.set_state(AIFlow.waiting_video_prompt)

    text = (
        "Параметры видео выбраны:\n"
        f"• duration: <b>{int(selected_duration_seconds)}s</b>\n"
        f"• size: <b>{escape(size)}</b>\n"
        f"• стоимость: <b>{price_info.tokens_price:.4f} токенов</b>\n\n"
        "Напишите промпт для генерации видео."
    )
    await callback.message.edit_text(text)
    await callback.answer("Размер выбран", show_alert=False)


@router.message(AIFlow.waiting_video_prompt, F.text)
async def generate_video_from_prompt(
    message: Message,
    video_generation_service: FromDishka[VideoGenerationService],
    state: FSMContext,
) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить Telegram пользователя")
        return

    prompt = (message.text or "").strip()
    if not prompt or prompt.startswith("/"):
        return

    fsm_data = await state.get_data()
    selected_model_id = fsm_data.get("selected_model_id")
    selected_model_type = fsm_data.get("selected_model_type")
    selected_duration_seconds = fsm_data.get("selected_video_duration_seconds")
    selected_size = fsm_data.get("selected_video_size")

    if selected_model_type != "video" or not selected_model_id:
        await message.answer("Сначала выбери video-модель.")
        return
    if not selected_duration_seconds or not selected_size:
        await message.answer("Сначала выбери duration и size.")
        return

    await message.answer("Генерирую видео, подожди немного…")

    try:
        result = await video_generation_service.generate_video(
            tg_user_id=message.from_user.id,
            model_id=UUID(selected_model_id),
            prompt=prompt,
            duration_seconds=int(selected_duration_seconds),
            size=str(selected_size),
        )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 402:
            await message.answer("Недостаточно токенов для этой генерации.")
        elif status_code == 401:
            await message.answer("Ошибка авторизации бота на backend.")
        else:
            await message.answer(f"Ошибка генерации видео: HTTP {status_code}")
        return
    except Exception:
        logger.exception("Failed to generate video")
        await message.answer("Ошибка генерации видео. Попробуй позже.")
        return

    await message.answer(
        "Готово ✅\n"
        f"Списано: <b>{result.tokens_cost:.4f} токенов</b>\n"
        "Отправляю видео..."
    )

    video_bytes: bytes | None = None
    try:
        video_bytes = await video_generation_service.get_video_generation_content(
            tg_user_id=message.from_user.id,
            generation_id=result.generation_id,
        )

        await message.answer_video(
            video=BufferedInputFile(
                file=video_bytes,
                filename=f"video_{result.generation_id}.mp4",
            ),
            caption=(
                "Видео готово ✅\n" f"Списано: <b>{result.tokens_cost:.4f} токенов</b>"
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
                filename=f"video_{result.generation_id}.mp4",
            ),
            caption=(
                "Видео готово ✅\n" f"Списано: <b>{result.tokens_cost:.4f} токенов</b>"
            ),
        )
    except httpx.HTTPStatusError as exc:
        logger.exception("Backend failed to return generated video content")
        await message.answer(
            f"Не удалось получить видео с backend: HTTP {exc.response.status_code}"
        )
    except Exception:
        logger.exception("Failed to download/send generated video")
        await message.answer("Не удалось отправить видео. Попробуй позже.")

    await state.set_state(AIFlow.choosing_model)
