from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from src.core.schemas import AIModelItem


MODE_LLM_TEXT = "💬 Чат-нейросети"
MODE_VIDEO_TEXT = "🎬 Генерация видео"
MODE_IMAGE_TEXT = "🎨 Генерация изображений"
BALANCE_BUTTON_TEXT = "💰 Баланс"
REFERRAL_BUTTON_TEXT = "🎁 Реферальная программа"
LLM_CONFIG_BUTTON_TEXT = "⚙️ Настройка инструкции для ИИ"
GENERATION_BUTTON_TEXT = "🚀 Генерация"


def build_model_types_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MODE_LLM_TEXT),
            ],
            [
                KeyboardButton(text=MODE_VIDEO_TEXT),
                KeyboardButton(text=MODE_IMAGE_TEXT),
            ],
            [
                KeyboardButton(text=BALANCE_BUTTON_TEXT),
            ],
            [
                KeyboardButton(text=REFERRAL_BUTTON_TEXT),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выбери режим нейросети",
    )


def build_ai_models_keyboard(
    models: list[AIModelItem],
    selected_model_id: str | None = None,
    include_llm_config_button: bool = False,
    include_generation_button: bool = False,
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
    if include_generation_button:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=GENERATION_BUTTON_TEXT,
                    callback_data="generation:start",
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


def build_image_sizes_keyboard(
    sizes: list[str],
    selected_size: str | None = None,
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=(f"✅ {size}" if size == selected_size else size),
                callback_data=f"image_size:{size}",
            )
        ]
        for size in sizes
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_image_qualities_keyboard(
    qualities: list[str],
    selected_quality: str | None = None,
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=(f"✅ {quality}" if quality == selected_quality else quality),
                callback_data=f"image_quality:{quality}",
            )
        ]
        for quality in qualities
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_video_durations_keyboard(
    durations_seconds: list[int],
    selected_duration_seconds: int | None = None,
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=(f"✅ {duration}s" if duration == selected_duration_seconds else f"{duration}s"),
                callback_data=f"video_duration:{duration}",
            )
        ]
        for duration in durations_seconds
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_video_sizes_keyboard(
    sizes: list[str],
    selected_size: str | None = None,
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=(f"✅ {size}" if size == selected_size else size),
                callback_data=f"video_size:{size}",
            )
        ]
        for size in sizes
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_balance_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Пополнить",
                    callback_data="balance:top_up",
                )
            ]
        ]
    )
