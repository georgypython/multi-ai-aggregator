from uuid import UUID

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka
import httpx

from src.core.logger import logger
from src.core.telegram_markdown import split_markdown_v2_safe
from src.handlers.ai_shared import AIFlowHelper
from src.services.llm_generation import LLMGenerationService
from src.states import AIFlow

router = Router()


@router.message(AIFlow.chatting_llm, F.text)
async def generate_for_selected_model(
    message: Message,
    llm_generation_service: FromDishka[LLMGenerationService],
    state: FSMContext,
) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя. Попробуй еще раз.")
        return

    text = (message.text or "").strip()
    if not text or text.startswith("/"):
        return
    if text in AIFlowHelper.MODE_TEXT_TO_TYPE:
        return

    fsm_data = await state.get_data()
    selected_model_id = fsm_data.get("selected_model_id")
    selected_model_type = fsm_data.get("selected_model_type")

    if selected_model_id is None or selected_model_type is None:
        await message.answer("Сначала выбери режим и модель, а потом отправь запрос ✨")
        return

    if selected_model_type != "llm":
        await message.answer(
            "Текстовый диалог доступен только в режиме LLM. Для image/video используй кнопку «Генерация» 🎬🖼️"
        )
        return

    try:
        result = await llm_generation_service.generate_llm_response(
            tg_user_id=message.from_user.id,
            model_id=UUID(selected_model_id),
            prompt=text,
        )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 402:
            await message.answer("Недостаточно токенов для этого запроса 💸")
        elif status_code == 401:
            await message.answer(
                "Сервис сейчас временно недоступен. Попробуй чуть позже."
            )
        elif status_code == 409:
            await message.answer(
                "С текущими настройками этот запрос не проходит. Попробуй скорректировать запрос или настройки."
            )
        else:
            await message.answer(
                "Не удалось сгенерировать ответ. Попробуй еще раз чуть позже."
            )
        return
    except Exception:
        logger.exception("Failed to generate LLM response")
        await message.answer("Ошибка генерации. Попробуй еще раз чуть позже.")
        return

    await state.set_state(AIFlow.chatting_llm)
    safe_chunks = split_markdown_v2_safe(result.text)
    for safe_chunk in safe_chunks:
        try:
            await message.answer(safe_chunk, parse_mode=ParseMode.MARKDOWN_V2)
        except TelegramBadRequest:
            logger.exception(
                "Telegram markdown_v2 parse failed for LLM response, falling back to plain text"
            )
            await message.answer(safe_chunk, parse_mode=None)
