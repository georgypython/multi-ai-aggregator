from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka
import httpx

from src.core.logger import logger
from src.handlers.ai_shared import AIFlowHelper
from src.keyboards.ai import build_ai_models_keyboard, build_model_types_keyboard
from src.services.ai import AIService
from src.states import AIFlow

router = Router()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AIFlow.choosing_mode)
    await message.answer(
        "Выбери режим:",
        reply_markup=build_model_types_keyboard(),
    )


@router.message(F.text.in_(tuple(AIFlowHelper.MODE_TEXT_TO_TYPE.keys())))
async def choose_model_type(
    message: Message,
    ai_service: FromDishka[AIService],
    state: FSMContext,
) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить Telegram пользователя")
        return

    model_type = AIFlowHelper.MODE_TEXT_TO_TYPE.get(message.text or "", "llm")

    try:
        models = await ai_service.get_models(
            tg_user_id=message.from_user.id,
            model_type=model_type,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            await message.answer("Ошибка авторизации бота на backend.")
        else:
            await message.answer(
                f"Не удалось загрузить модели: HTTP {exc.response.status_code}"
            )
        return
    except Exception:
        logger.exception("Failed to fetch AI models from backend")
        await message.answer("Не удалось загрузить модели. Попробуй позже.")
        return

    if not models:
        await message.answer("Для этого раздела пока нет доступных моделей.")
        return

    fsm_data = await state.get_data()
    selected_model_id: str | None = fsm_data.get("selected_model_id")
    selected_model = next(
        (model for model in models if str(model.id) == selected_model_id), None
    )
    if selected_model is None:
        selected_model = models[0]

    await state.update_data(
        selected_mode=model_type,
        selected_model_id=str(selected_model.id),
        selected_model_name=selected_model.name,
        selected_model_type=selected_model.model_type.lower(),
        last_models=AIFlowHelper.serialize_models(models),
    )
    if selected_model.model_type.lower() == "llm":
        await state.set_state(AIFlow.chatting_llm)
    else:
        await state.set_state(AIFlow.choosing_model)

    models_text = AIFlowHelper.render_models_text(
        models=models,
        current_model_name=selected_model.name,
    )
    models_keyboard = build_ai_models_keyboard(
        models=models,
        selected_model_id=str(selected_model.id),
        include_llm_config_button=(model_type == "llm"),
        include_generation_button=(model_type in ("image", "video")),
    )
    await message.answer(models_text, reply_markup=models_keyboard)
