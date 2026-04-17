from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from src.core.schemas import AIModelItem, PaymentProductItem

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
                text=(
                    f"✅ {model.name}"
                    if str(model.id) == selected_model_id
                    else model.name
                ),
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
                text=(
                    f"✅ {duration}s"
                    if duration == selected_duration_seconds
                    else f"{duration}s"
                ),
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


def build_balance_products_keyboard(
    products: list[PaymentProductItem],
    current_index: int,
) -> InlineKeyboardMarkup:
    total = len(products)
    prev_index = (current_index - 1) % total
    next_index = (current_index + 1) % total
    current = products[current_index]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ Выбрать тариф {current.name}",
                    callback_data=f"balance:product:select:{current.plan_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"balance:product:nav:{prev_index}",
                ),
                InlineKeyboardButton(
                    text=f"{current_index + 1}/{total}",
                    callback_data="balance:product:noop",
                ),
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"balance:product:nav:{next_index}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад к балансу",
                    callback_data="balance:back",
                )
            ],
        ]
    )


def build_payment_methods_keyboard(
    methods: list[tuple[str, str]],
    plan_index: int,
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f"balance:method:pick:{plan_index}:{code}",
            )
        ]
        for code, label in methods
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ К тарифам",
                callback_data="balance:top_up",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_balance_checkout_keyboard(plan_index: int, payment_method: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Оплатить",
                    callback_data=f"balance:pay:{plan_index}:{payment_method}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ К способам оплаты",
                    callback_data=f"balance:method:back:{plan_index}",
                )
            ],
        ]
    )


def build_balance_payment_link_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Оплатить по ссылке", url=payment_url)],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к балансу",
                    callback_data="balance:back",
                )
            ],
        ]
    )
