from uuid import UUID
from io import BytesIO

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types.input_file import BufferedInputFile
from dishka.integrations.aiogram import FromDishka
import httpx

from src.core.schemas import GenerationStatus
from src.core.logger import logger
from src.services.ai import AIService
from src.services.video_generation import VideoGenerationService
from src.states import AIFlow

router = Router()


@router.callback_query(F.data.startswith("video_duration:"))
async def choose_video_duration(
    callback: CallbackQuery,
    ai_service: FromDishka[AIService],
    state: FSMContext,
) -> None:
    if callback.message is None:
        await callback.answer("Сообщение не найдено", show_alert=False)
        return

    fsm_data = await state.get_data()
    selected_model_type = fsm_data.get("selected_model_type")
    if selected_model_type != "video":
        await callback.answer("Сейчас открыт другой режим", show_alert=False)
        return

    durations_seconds: list[int] = fsm_data.get("selected_video_durations_seconds", [])
    if not durations_seconds:
        await callback.answer("Сначала выбери видеомодель", show_alert=False)
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
    selected_model_id = fsm_data.get("selected_model_id")
    selected_model_type = fsm_data.get("selected_model_type")

    if (
        callback.from_user is None
        or selected_model_type != "video"
        or not selected_model_id
    ):
        await callback.answer("Сначала выбери видеомодель", show_alert=False)
        return

    try:
        price_info = await ai_service.get_video_model_price(
            tg_user_id=callback.from_user.id,
            model_id=UUID(selected_model_id),
            duration_seconds=duration_seconds,
        )
    except httpx.HTTPStatusError as exc:
        await callback.answer(
            "Не удалось рассчитать стоимость. Попробуй еще раз.",
            show_alert=True,
        )
        return
    except Exception:
        logger.exception("Failed to get video model price")
        await callback.answer("Не удалось рассчитать стоимость", show_alert=True)
        return

    await state.update_data(
        selected_video_tokens_price=price_info.tokens_price,
    )
    await state.set_state(AIFlow.waiting_video_prompt)

    text = (
        "<b>Параметры видео готовы 🎬</b>\n"
        f"• Длительность: <b>{duration_seconds}s</b>\n"
        f"• Стоимость: <b>{price_info.tokens_price:.4f} токенов</b>\n\n"
        "Напиши запрос текстом\n"
        "или прикрепи картинку с подписью, если хочешь сделать видео по этой картинке.\n\n"
        "Пример подписи к фото:\n"
        "<i>Камера медленно приближается, кинематографичное освещение, 6 секунд</i>"
    )
    await callback.message.edit_text(text)
    await callback.answer("Длительность выбрана", show_alert=False)


@router.message(AIFlow.waiting_video_prompt, F.text)
async def generate_video_from_prompt(
    message: Message,
    video_generation_service: FromDishka[VideoGenerationService],
    state: FSMContext,
) -> None:
    prompt = (message.text or "").strip()
    if not prompt or prompt.startswith("/"):
        return

    await _run_video_generation(
        message=message,
        video_generation_service=video_generation_service,
        state=state,
        prompt=prompt,
    )


async def _collect_photo_attachment(message: Message) -> tuple[str, bytes, str] | None:
    if not message.photo:
        return None

    photo = message.photo[-1]
    tg_file = await message.bot.get_file(photo.file_id)
    buffer = BytesIO()
    await message.bot.download_file(tg_file.file_path, destination=buffer)
    file_bytes = buffer.getvalue()
    if not file_bytes:
        return None

    return (f"{photo.file_unique_id}.jpg", file_bytes, "image/jpeg")


async def _run_video_generation(
    message: Message,
    video_generation_service: FromDishka[VideoGenerationService],
    state: FSMContext,
    prompt: str,
    image_attachment: tuple[str, bytes, str] | None = None,
) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя. Попробуй еще раз.")
        return

    fsm_data = await state.get_data()
    selected_model_id = fsm_data.get("selected_model_id")
    selected_model_type = fsm_data.get("selected_model_type")
    selected_duration_seconds = fsm_data.get("selected_video_duration_seconds")

    if selected_model_type != "video" or not selected_model_id:
        await message.answer("Сначала выбери видеомодель.")
        return
    if not selected_duration_seconds:
        await message.answer("Сначала выбери длительность видео.")
        return

    media_file_id: UUID | None = None
    if image_attachment:
        try:
            upload_result = await video_generation_service.upload_image(
                tg_user_id=message.from_user.id,
                file=image_attachment,
            )
            media_file_id = upload_result.media_file_id
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code == 413:
                await message.answer(
                    "Файл слишком большой. Попробуй изображение меньшего размера."
                )
            elif status_code == 400:
                await message.answer("Неподдерживаемый формат изображения.")
            elif status_code == 401:
                await message.answer(
                    "Сервис сейчас временно недоступен. Попробуй чуть позже."
                )
            else:
                await message.answer(
                    "Не удалось загрузить изображение. Попробуй позже."
                )
            return
        except Exception:
            logger.exception("Failed to upload image before video generation")
            await message.answer("Не удалось загрузить изображение. Попробуй позже.")
            return

    await message.answer("Принял запрос ✨ Запускаю генерацию видео...")

    try:
        result = await video_generation_service.generate_video(
            tg_user_id=message.from_user.id,
            model_id=UUID(selected_model_id),
            prompt=prompt,
            duration_seconds=int(selected_duration_seconds),
            media_file_id=media_file_id,
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
        return
    except Exception:
        logger.exception("Failed to generate video")
        await message.answer("Ошибка генерации видео. Попробуй позже.")
        return

    await message.answer("Генерация запущена ⏳ Обычно это занимает до пары минут.")

    try:
        final_status = await video_generation_service.wait_for_video_generation_status(
            tg_user_id=message.from_user.id,
            generation_id=result.generation_id,
        )
    except httpx.HTTPStatusError as exc:
        logger.exception("Backend failed while polling video generation status")
        await message.answer(
            "Не удалось проверить прогресс генерации. Попробуй немного позже."
        )
        return
    except TimeoutError:
        await message.answer(
            "Генерация заняла слишком много времени. Попробуй еще раз чуть позже ⏱️"
        )
        return
    except Exception:
        logger.exception("Failed while polling video generation status")
        await message.answer("Не удалось проверить прогресс генерации. Попробуй позже.")
        return

    if final_status.status == GenerationStatus.FAILED:
        await message.answer(
            "Не удалось завершить генерацию видео ❌ Попробуй другой запрос."
        )
        return

    if final_status.status == GenerationStatus.CANCELED:
        await message.answer("Генерация была отменена ❌")
        return

    if final_status.status != GenerationStatus.COMPLETED:
        await message.answer("Видео еще готовится. Проверь чуть позже ⏳")
        return

    await message.answer(
        "<b>Готово ✅</b>\n"
        f"Списано: <b>{final_status.tokens_cost:.4f} токенов</b>\n"
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
                filename=f"video_{result.generation_id}.mp4",
            ),
            caption=(
                "<b>Видео готово ✅</b>\n"
                f"Списано: <b>{final_status.tokens_cost:.4f} токенов</b>"
            ),
        )
    except httpx.HTTPStatusError as exc:
        logger.exception("Backend failed to return generated video content")
        await message.answer("Не удалось получить готовое видео. Попробуй позже.")
    except Exception:
        logger.exception("Failed to download/send generated video")
        await message.answer("Не удалось отправить видео. Попробуй позже.")

    await state.set_state(AIFlow.choosing_model)


@router.message(AIFlow.waiting_video_prompt, F.photo)
async def generate_video_from_photo(
    message: Message,
    video_generation_service: FromDishka[VideoGenerationService],
    state: FSMContext,
) -> None:
    prompt = (message.caption or "").strip()
    if not prompt:
        await message.answer(
            "Добавь подпись к фото — по ней будет сгенерировано видео.\n"
            "Например: <i>Плавный пролёт камеры, вечерний город, кино, 6 секунд</i>"
        )
        return

    attachment = await _collect_photo_attachment(message)
    if attachment is None:
        await message.answer("Не удалось прочитать изображение из сообщения.")
        return

    await _run_video_generation(
        message=message,
        video_generation_service=video_generation_service,
        state=state,
        prompt=prompt,
        image_attachment=attachment,
    )
