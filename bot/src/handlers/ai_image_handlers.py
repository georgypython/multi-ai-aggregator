from io import BytesIO
from html import escape
from uuid import UUID

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types.input_file import BufferedInputFile
from dishka.integrations.aiogram import FromDishka
import httpx

from src.core.schemas import GenerationStatus
from src.core.logger import logger
from src.keyboards.ai import build_image_qualities_keyboard
from src.services.ai import AIService
from src.services.image_generation import ImageGenerationService
from src.states import AIFlow

router = Router()


@router.callback_query(F.data.startswith("image_size:"))
async def choose_image_size(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if callback.message is None:
        await callback.answer("Сообщение не найдено", show_alert=False)
        return

    fsm_data = await state.get_data()
    selected_model_type = fsm_data.get("selected_model_type")
    if selected_model_type != "image":
        await callback.answer("Сейчас открыт другой режим", show_alert=False)
        return

    sizes: list[str] = fsm_data.get("selected_image_sizes", [])
    if not sizes:
        await callback.answer("Сначала выбери модель изображения", show_alert=False)
        return

    size = (callback.data or "").split(":", maxsplit=1)[1] if callback.data else None
    if not size:
        await callback.answer("Размер не распознан", show_alert=False)
        return

    if size not in sizes:
        await callback.answer("Недоступный размер", show_alert=False)
        return

    await state.update_data(selected_image_size=size)
    await state.set_state(AIFlow.choosing_image_quality)

    qualities: list[str] = fsm_data.get("selected_image_qualities", [])
    if not qualities:
        await callback.answer(
            "Не удалось загрузить параметры качества", show_alert=True
        )
        return

    await callback.message.edit_text(
        f"<b>Шаг 2/2</b>\nРазмер: <b>{escape(size)}</b>\nТеперь выбери качество:",
        reply_markup=build_image_qualities_keyboard(qualities),
    )
    await callback.answer("Размер выбран", show_alert=False)


@router.callback_query(F.data.startswith("image_quality:"))
async def choose_image_quality(
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
    selected_size = fsm_data.get("selected_image_size")

    if selected_model_type != "image" or not selected_model_id:
        await callback.answer("Сначала выбери модель изображения", show_alert=False)
        return
    if not selected_size:
        await callback.answer("Сначала выбери размер", show_alert=False)
        return

    quality = (callback.data or "").split(":", maxsplit=1)[1] if callback.data else None
    if not quality:
        await callback.answer("Качество не распознано", show_alert=False)
        return

    try:
        price_info = await ai_service.get_image_model_price(
            tg_user_id=callback.from_user.id,
            model_id=UUID(selected_model_id),
            size=selected_size,
            quality=quality,
        )
    except httpx.HTTPStatusError as exc:
        await callback.answer(
            "Не удалось рассчитать стоимость. Попробуй еще раз.",
            show_alert=True,
        )
        return
    except Exception:
        logger.exception("Failed to get image model price")
        await callback.answer("Не удалось рассчитать стоимость", show_alert=True)
        return

    await state.update_data(
        selected_image_quality=quality,
        selected_image_tokens_price=price_info.tokens_price,
    )
    await state.set_state(AIFlow.waiting_image_prompt)

    text = (
        "<b>Параметры изображения готовы 🖼️</b>\n"
        f"• Размер: <b>{escape(selected_size)}</b>\n"
        f"• Качество: <b>{escape(quality)}</b>\n"
        f"• Стоимость: <b>{price_info.tokens_price:.4f} токенов</b>\n\n"
        "Отправь промпт текстом или фото с подписью."
    )
    await callback.message.edit_text(text)
    await callback.answer("Качество выбрано", show_alert=False)


async def _run_image_generation(
    message: Message,
    image_generation_service: FromDishka[ImageGenerationService],
    state: FSMContext,
    prompt: str,
    image_attachments: list[tuple[str, bytes, str]] | None = None,
) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя. Попробуй еще раз.")
        return

    fsm_data = await state.get_data()
    selected_model_id = fsm_data.get("selected_model_id")
    selected_model_type = fsm_data.get("selected_model_type")
    selected_size = fsm_data.get("selected_image_size")
    selected_quality = fsm_data.get("selected_image_quality")

    if selected_model_type != "image" or not selected_model_id:
        await message.answer("Сначала выбери модель изображения.")
        return
    if not selected_size or not selected_quality:
        await message.answer("Сначала выбери размер и качество.")
        return

    media_file_ids: list[UUID] | None = None
    if image_attachments:
        try:
            upload_result = await image_generation_service.upload_image(
                tg_user_id=message.from_user.id,
                file=image_attachments[0],
            )
            media_file_ids = [upload_result.media_file_id]
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
            logger.exception("Failed to upload images before generation")
            await message.answer("Не удалось загрузить изображение. Попробуй позже.")
            return

    await message.answer("Принял запрос ✨ Запускаю генерацию изображения...")

    try:
        result = await image_generation_service.generate_image(
            tg_user_id=message.from_user.id,
            model_id=UUID(selected_model_id),
            prompt=prompt,
            size=selected_size,
            quality=selected_quality,
            media_file_ids=media_file_ids,
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
                "Не удалось запустить генерацию изображения. Попробуй позже."
            )
        return
    except Exception:
        logger.exception("Failed to generate image")
        await message.answer(
            "Не удалось запустить генерацию изображения. Попробуй позже."
        )
        return

    await message.answer("Генерация запущена ⏳ Обычно это занимает до минуты.")

    try:
        final_status = await image_generation_service.wait_for_image_generation_status(
            tg_user_id=message.from_user.id,
            generation_id=result.generation_id,
        )
    except httpx.HTTPStatusError as exc:
        logger.exception("Backend failed while polling image generation status")
        await message.answer(
            "Не удалось проверить прогресс генерации. Попробуй немного позже."
        )
        return
    except TimeoutError:
        await message.answer(
            "Генерация заняла слишком много времени. Попробуй еще раз чуть позже."
        )
        return
    except Exception:
        logger.exception("Failed while polling image generation status")
        await message.answer("Не удалось проверить прогресс генерации. Попробуй позже.")
        return

    if final_status.status == GenerationStatus.FAILED:
        await message.answer(
            "Не удалось завершить генерацию изображения ❌ Попробуй другой запрос."
        )
        return

    if final_status.status == GenerationStatus.CANCELED:
        await message.answer("Генерация была отменена ❌")
        return

    if final_status.status != GenerationStatus.COMPLETED:
        await message.answer("Изображение еще готовится. Проверь чуть позже ⏳")
        return

    await message.answer(
        "<b>Готово ✅</b>\n"
        f"Списано: <b>{final_status.tokens_cost:.4f} токенов</b>\n"
        "Отправляю изображение..."
    )

    try:
        image_bytes = await image_generation_service.get_image_generation_content(
            tg_user_id=message.from_user.id,
            generation_id=result.generation_id,
        )

        await message.answer_photo(
            photo=BufferedInputFile(
                file=image_bytes,
                filename=f"image_{result.generation_id}.jpg",
            ),
            caption=(
                "<b>Изображение готово ✅</b>\n"
                f"Списано: <b>{final_status.tokens_cost:.4f} токенов</b>"
            ),
        )
    except TelegramBadRequest:
        logger.exception("Telegram failed to process image as photo")
        await message.answer_document(
            document=BufferedInputFile(
                file=image_bytes,
                filename=f"image_{result.generation_id}.jpg",
            ),
            caption=(
                "<b>Изображение готово ✅</b>\n"
                f"Списано: <b>{final_status.tokens_cost:.4f} токенов</b>"
            ),
        )
    except httpx.HTTPStatusError as exc:
        logger.exception("Backend failed to return generated image content")
        await message.answer("Не удалось получить готовое изображение. Попробуй позже.")
    except Exception:
        logger.exception("Failed to download/send generated image")
        await message.answer("Не удалось отправить изображение. Попробуй позже.")

    await state.set_state(AIFlow.choosing_model)


async def _collect_photo_attachments(
    messages: list[Message],
) -> list[tuple[str, bytes, str]]:
    attachments: list[tuple[str, bytes, str]] = []

    for item in messages:
        if not item.photo:
            continue

        photo = item.photo[-1]
        tg_file = await item.bot.get_file(photo.file_id)
        buffer = BytesIO()
        await item.bot.download_file(tg_file.file_path, destination=buffer)
        file_bytes = buffer.getvalue()
        if not file_bytes:
            continue

        attachments.append((f"{photo.file_unique_id}.jpg", file_bytes, "image/jpeg"))

    return attachments


@router.message(AIFlow.waiting_image_prompt, F.text)
async def generate_image_from_prompt_text(
    message: Message,
    image_generation_service: FromDishka[ImageGenerationService],
    state: FSMContext,
) -> None:
    prompt = (message.text or "").strip()
    if not prompt or prompt.startswith("/"):
        return

    await _run_image_generation(
        message=message,
        image_generation_service=image_generation_service,
        state=state,
        prompt=prompt,
    )


@router.message(AIFlow.waiting_image_prompt, F.photo)
async def generate_image_from_single_photo(
    message: Message,
    image_generation_service: FromDishka[ImageGenerationService],
    state: FSMContext,
) -> None:
    prompt = (message.caption or "").strip()
    if not prompt:
        await message.answer("Добавь подпись к фото — это и будет prompt.")
        return

    attachments = await _collect_photo_attachments([message])
    if not attachments:
        await message.answer("Не удалось прочитать изображение из сообщения.")
        return

    await _run_image_generation(
        message=message,
        image_generation_service=image_generation_service,
        state=state,
        prompt=prompt,
        image_attachments=attachments,
    )
