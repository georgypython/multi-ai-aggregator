from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from src.services.ai import AIModelItem


MODE_LLM_TEXT = "💬 Чат-нейросети"
MODE_VIDEO_TEXT = "🎬 Генерация видео"
MODE_IMAGE_TEXT = "🎨 Генерация изображений"
LLM_CONFIG_BUTTON_TEXT = "⚙️ Настройка инструкции для ИИ"


def build_model_types_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MODE_LLM_TEXT),
                KeyboardButton(text=MODE_VIDEO_TEXT),
                KeyboardButton(text=MODE_IMAGE_TEXT),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выбери режим нейросети",
    )


def build_ai_models_keyboard(
    models: list[AIModelItem],
    *,
    selected_model_id: str | None = None,
    include_llm_config_button: bool = False,
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=(f"✅ {model.name}" if str(model.id) == selected_model_id else model.name),
                callback_data=f"model:{model.id}",
            )
        ]
        for model in models
    ]
    if include_llm_config_button:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=LLM_CONFIG_BUTTON_TEXT,
                    callback_data="llm_config:open",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_llm_config_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Изменить температуру",
                    callback_data="llm_config:set_temperature",
                ),
                InlineKeyboardButton(
                    text="Изменить инструкции",
                    callback_data="llm_config:set_instructions",
                ),
            ]
        ]
    )
