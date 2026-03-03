from html import escape
from uuid import UUID

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka

from src.core.logger import logger
from src.handlers.ai_shared import MODE_TEXT_TO_TYPE
from src.services.ai import AIService, BackendAPIError
from src.states import AIFlow


router = Router()


@router.message(F.text)
async def generate_for_selected_model(
    message: Message,
    ai_service: FromDishka[AIService],
    state: FSMContext,
) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить Telegram пользователя")
        return

    text = (message.text or "").strip()
    if not text or text.startswith("/"):
        return
    if text in MODE_TEXT_TO_TYPE:
        return

    fsm_data = await state.get_data()
    selected_model_id = fsm_data.get("selected_model_id")
    selected_model_type = fsm_data.get("selected_model_type")

    if selected_model_id is None or selected_model_type is None:
        await message.answer("Сначала выбери режим и модель.")
        return

    if selected_model_type != "llm":
        await message.answer("Для видео/изображений генерация текста пока не подключена.")
        return

    try:
        result = await ai_service.generate_llm_response(
            tg_user_id=message.from_user.id,
            model_id=UUID(selected_model_id),
            prompt=text,
        )
    except BackendAPIError as exc:
        if exc.status_code == 402:
            await message.answer("Недостаточно токенов для этой модели.")
        elif exc.status_code == 401:
            await message.answer("Ошибка авторизации бота на backend.")
        elif exc.status_code == 409:
            await message.answer(exc.detail)
        else:
            await message.answer(f"Ошибка генерации: {exc.detail}")
        return
    except Exception:
        logger.exception("Failed to generate LLM response")
        await message.answer("Ошибка генерации. Попробуй позже.")
        return

    await state.set_state(AIFlow.chatting_llm)
    await message.answer(escape(result.text))
