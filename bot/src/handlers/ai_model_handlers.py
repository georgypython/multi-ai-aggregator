from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import FromDishka
import httpx

from src.handlers.ai_shared import AIFlowHelper
from src.keyboards.ai import build_ai_models_keyboard, build_image_sizes_keyboard
from src.services.ai import AIService
from src.states import AIFlow


router = Router()


@router.callback_query(F.data.startswith("model:"))
async def choose_model(
    callback: CallbackQuery,
    state: FSMContext,
    ai_service: FromDishka[AIService],
) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer("Не удалось определить пользователя", show_alert=True)
        return

    fsm_data = await state.get_data()
    last_models_raw: list[dict] = fsm_data.get("last_models", [])
    if not last_models_raw:
        await callback.answer("Сначала выбери режим", show_alert=False)
        return

    last_models = AIFlowHelper.deserialize_models(last_models_raw)
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
    if (
        current_selected_model_id == str(selected_model.id)
        and selected_model.model_type.lower() == "llm"
    ):
        await callback.answer("Эта модель уже выбрана", show_alert=False)
        return

    await state.update_data(
        selected_model_id=str(selected_model.id),
        selected_model_name=selected_model.name,
        selected_model_type=selected_model.model_type.lower(),
        selected_image_size=None,
        selected_image_quality=None,
        selected_image_tokens_price=None,
    )

    selected_type = selected_model.model_type.lower()
    if selected_type == "llm":
        await state.set_state(AIFlow.chatting_llm)

        updated_text = AIFlowHelper.render_models_text(
            models=last_models,
            current_model_name=selected_model.name,
        )
        updated_keyboard = build_ai_models_keyboard(
            models=last_models,
            selected_model_id=str(selected_model.id),
            include_llm_config_button=True,
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
        return

    if selected_type == "image":
        try:
            image_config = await ai_service.get_image_model_config(model_id=selected_model.id)
        except httpx.HTTPStatusError as exc:
            await callback.answer(
                f"Ошибка загрузки модели: HTTP {exc.response.status_code}",
                show_alert=True,
            )
            return

        await state.update_data(
            selected_image_sizes=image_config.sizes,
            selected_image_qualities=image_config.qualities,
        )
        await state.set_state(AIFlow.choosing_image_size)

        text = (
            f"Выбрана image-модель: <b>{selected_model.name}</b>\n"
            f"Выбери размер изображения:"
        )
        try:
            await callback.message.edit_text(
                text,
                reply_markup=build_image_sizes_keyboard(image_config.sizes),
            )
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc):
                raise
        await callback.answer("Выбери размер", show_alert=False)
        return

    await state.set_state(AIFlow.choosing_model)
    await callback.answer(
        "Для этого типа модели flow пока не подключен.",
        show_alert=False,
    )
