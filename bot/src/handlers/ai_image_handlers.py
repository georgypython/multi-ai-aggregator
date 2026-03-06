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
        await callback.answer("Это не image flow", show_alert=False)
        return

    sizes: list[str] = fsm_data.get("selected_image_sizes", [])
    if not sizes:
        await callback.answer("Сначала выбери image-модель", show_alert=False)
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
        await callback.answer("Не найдены quality для модели", show_alert=True)
        return

    await callback.message.edit_text(
        f"Размер: <b>{escape(size)}</b>\nВыбери quality:",
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
        await callback.answer("Сначала выбери image-модель", show_alert=False)
        return
    if not selected_size:
        await callback.answer("Сначала выбери размер", show_alert=False)
        return

    quality = (callback.data or "").split(":", maxsplit=1)[1] if callback.data else None
    if not quality:
        await callback.answer("Quality не распознан", show_alert=False)
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
            f"Ошибка цены: HTTP {exc.response.status_code}",
            show_alert=True,
        )
        return
    except Exception:
        logger.exception("Failed to get image model price")
        await callback.answer("Ошибка при расчете цены", show_alert=True)
        return

    await state.update_data(
        selected_image_quality=quality,
        selected_image_tokens_price=price_info.tokens_price,
    )
    await state.set_state(AIFlow.waiting_image_prompt)

    text = (
        "Параметры изображения выбраны:\n"
        f"• size: <b>{escape(selected_size)}</b>\n"
        f"• quality: <b>{escape(quality)}</b>\n"
        f"• стоимость: <b>{price_info.tokens_price:.4f} токенов</b>\n\n"
        "Напишите промпт для генерации изображения."
    )
    await callback.message.edit_text(text)
    await callback.answer("Quality выбран", show_alert=False)


@router.message(AIFlow.waiting_image_prompt, F.text)
async def generate_image_from_prompt(
    message: Message,
    image_generation_service: FromDishka[ImageGenerationService],
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
    selected_size = fsm_data.get("selected_image_size")
    selected_quality = fsm_data.get("selected_image_quality")

    if selected_model_type != "image" or not selected_model_id:
        await message.answer("Сначала выбери image-модель.")
        return
    if not selected_size or not selected_quality:
        await message.answer("Сначала выбери size и quality.")
        return

    await message.answer("Генерирую изображение, подожди немного…")

    try:
        result = await image_generation_service.generate_image(
            tg_user_id=message.from_user.id,
            model_id=UUID(selected_model_id),
            prompt=prompt,
            size=selected_size,
            quality=selected_quality,
        )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 402:
            await message.answer("Недостаточно токенов для этой генерации.")
        elif status_code == 401:
            await message.answer("Ошибка авторизации бота на backend.")
        else:
            await message.answer(f"Ошибка генерации изображения: HTTP {status_code}")
        return
    except Exception:
        logger.exception("Failed to generate image")
        await message.answer("Ошибка генерации изображения. Попробуй позже.")
        return

    await message.answer(
        "Готово ✅\n"
        f"Списано: <b>{result.tokens_cost:.4f} токенов</b>\n"
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
                "Изображение готово ✅\n"
                f"Списано: <b>{result.tokens_cost:.4f} токенов</b>"
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
                "Изображение готово ✅\n"
                f"Списано: <b>{result.tokens_cost:.4f} токенов</b>"
            ),
        )
    except httpx.HTTPStatusError as exc:
        logger.exception("Backend failed to return generated image content")
        await message.answer(
            f"Не удалось получить изображение с backend: HTTP {exc.response.status_code}"
        )
    except Exception:
        logger.exception("Failed to download/send generated image")
        await message.answer("Не удалось отправить изображение. Попробуй позже.")

    await state.set_state(AIFlow.choosing_model)
