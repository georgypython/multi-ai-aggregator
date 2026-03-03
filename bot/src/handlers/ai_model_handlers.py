from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.handlers.ai_shared import deserialize_models, render_models_text
from src.keyboards.ai import build_ai_models_keyboard
from src.states import AIFlow


router = Router()


@router.callback_query(F.data.startswith("model:"))
async def choose_model(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer("Не удалось определить пользователя", show_alert=True)
        return

    fsm_data = await state.get_data()
    last_models_raw: list[dict] = fsm_data.get("last_models", [])
    if not last_models_raw:
        await callback.answer("Сначала выбери режим", show_alert=False)
        return

    last_models = deserialize_models(last_models_raw)
    selected_model_id = (callback.data or "").split(":", maxsplit=1)[1] if callback.data else None
    if not selected_model_id:
        await callback.answer("Модель не распознана", show_alert=False)
        return

    selected_model = next(
        (model for model in last_models if str(model.id) == selected_model_id),
        None,
    )
    if selected_model is None:
        await callback.answer("Модель не найдена", show_alert=False)
        return

    current_selected_model_id = fsm_data.get("selected_model_id")
    if current_selected_model_id == str(selected_model.id):
        await callback.answer("Эта модель уже выбрана", show_alert=False)
        return

    await state.update_data(
        selected_model_id=str(selected_model.id),
        selected_model_name=selected_model.name,
        selected_model_type=selected_model.model_type.lower(),
    )
    if selected_model.model_type.lower() == "llm":
        await state.set_state(AIFlow.chatting_llm)
    else:
        await state.set_state(AIFlow.choosing_model)

    updated_text = render_models_text(
        models=last_models,
        current_model_name=selected_model.name,
    )
    updated_keyboard = build_ai_models_keyboard(
        models=last_models,
        selected_model_id=str(selected_model.id),
        include_llm_config_button=(selected_model.model_type.lower() == "llm"),
    )
    try:
        await callback.message.edit_text(
            updated_text,
            reply_markup=updated_keyboard,
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise
    await callback.answer(f"Выбрана модель: {selected_model.name}", show_alert=False)
