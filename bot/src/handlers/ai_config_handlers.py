from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka
import httpx

from src.core.logger import logger
from src.handlers.ai_shared import AIFlowHelper
from src.keyboards.ai import build_llm_config_keyboard
from src.services.ai import AIService
from src.services.llm_generation import LLMGenerationService
from src.states import AIFlow

router = Router()


@router.callback_query(F.data == "llm_config:open")
async def open_llm_config(
    callback: CallbackQuery,
    ai_service: FromDishka[AIService],
    state: FSMContext,
) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer("Не удалось определить пользователя", show_alert=True)
        return

    fsm_data = await state.get_data()
    selected_model_type = fsm_data.get("selected_model_type")
    if selected_model_type != "llm":
        await callback.answer("Настройки доступны только для LLM", show_alert=False)
        return

    try:
        config = await ai_service.get_llm_config(tg_user_id=callback.from_user.id)
        temperature = config.temperature
        instructions = config.instructions
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 404:
            temperature = None
            instructions = None
        elif status_code == 401:
            await callback.answer(
                "Сервис сейчас временно недоступен. Попробуй чуть позже.",
                show_alert=True,
            )
            return
        else:
            await callback.answer(
                "Не удалось загрузить настройки. Попробуй позже.", show_alert=True
            )
            return
    except Exception:
        logger.exception("Failed to fetch LLM config")
        await callback.answer("Не удалось открыть настройки", show_alert=True)
        return

    config_text = AIFlowHelper.render_llm_config_text(
        temperature=temperature,
        instructions=instructions,
    )
    try:
        await callback.message.edit_text(
            config_text,
            reply_markup=build_llm_config_keyboard(),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise
    await callback.answer()


@router.callback_query(F.data == "llm_config:set_temperature")
async def ask_temperature(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if callback.message is None:
        await callback.answer("Сообщение не найдено", show_alert=False)
        return

    await state.set_state(AIFlow.editing_llm_temperature)
    await callback.message.answer(
        "<b>Температура</b>\n"
        "Введи число от 0.0 до 2.0\n"
        "• 0.0-1.0: более точно 🎯\n"
        "• 1.0-2.0: более креативно ✨"
    )
    await callback.answer()


@router.callback_query(F.data == "llm_config:set_instructions")
async def ask_instructions(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if callback.message is None:
        await callback.answer("Сообщение не найдено", show_alert=False)
        return

    await state.set_state(AIFlow.editing_llm_instructions)
    await callback.message.answer(
        "<b>Инструкции для ИИ</b>\n"
        "Напиши, как ассистент должен отвечать: стиль, тон, формат ✍️"
    )
    await callback.answer()


@router.message(AIFlow.editing_llm_temperature, F.text)
async def save_temperature(
    message: Message,
    llm_generation_service: FromDishka[LLMGenerationService],
    state: FSMContext,
) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя. Попробуй еще раз.")
        return

    raw_value = (message.text or "").strip().replace(",", ".")
    try:
        temperature = float(raw_value)
    except ValueError:
        await message.answer("Нужно число от 0.0 до 2.0. Попробуй еще раз.")
        return

    if temperature < 0.0 or temperature > 2.0:
        await message.answer("Температура должна быть в диапазоне от 0.0 до 2.0")
        return

    try:
        config = await llm_generation_service.create_or_update_llm_config(
            tg_user_id=message.from_user.id,
            temperature=temperature,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            await message.answer(
                "Сервис сейчас временно недоступен. Попробуй чуть позже."
            )
        else:
            await message.answer("Не удалось сохранить температуру. Попробуй позже.")
        return
    except Exception:
        logger.exception("Failed to save LLM temperature")
        await message.answer("Не удалось сохранить температуру. Попробуй позже.")
        return

    await state.set_state(AIFlow.chatting_llm)
    await message.answer(
        AIFlowHelper.render_llm_config_text(
            temperature=config.temperature,
            instructions=config.instructions,
        ),
        reply_markup=build_llm_config_keyboard(),
    )


@router.message(AIFlow.editing_llm_instructions, F.text)
async def save_instructions(
    message: Message,
    llm_generation_service: FromDishka[LLMGenerationService],
    state: FSMContext,
) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя. Попробуй еще раз.")
        return

    instructions = (message.text or "").strip()
    if not instructions:
        await message.answer("Инструкции не должны быть пустыми. Попробуй еще раз.")
        return

    try:
        config = await llm_generation_service.create_or_update_llm_config(
            tg_user_id=message.from_user.id,
            instructions=instructions,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            await message.answer(
                "Сервис сейчас временно недоступен. Попробуй чуть позже."
            )
        else:
            await message.answer("Не удалось сохранить инструкции. Попробуй позже.")
        return
    except Exception:
        logger.exception("Failed to save LLM instructions")
        await message.answer("Не удалось сохранить инструкции. Попробуй позже.")
        return

    await state.set_state(AIFlow.chatting_llm)
    await message.answer(
        AIFlowHelper.render_llm_config_text(
            temperature=config.temperature,
            instructions=config.instructions,
        ),
        reply_markup=build_llm_config_keyboard(),
    )
