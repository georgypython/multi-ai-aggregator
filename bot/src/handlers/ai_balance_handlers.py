from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka
import httpx

from src.core.logger import logger
from src.core.schemas import PaymentProductItem
from src.keyboards.ai import (
    BALANCE_BUTTON_TEXT,
    REFERRAL_BUTTON_TEXT,
    build_balance_keyboard,
    build_balance_checkout_keyboard,
    build_payment_methods_keyboard,
    build_balance_payment_link_keyboard,
    build_balance_products_keyboard,
)
from src.services.ai import AIService

router = Router()


LLM_TOKENS_PER_GEN = 0.108
IMAGE_TOKENS_PER_GEN = 1.08
VIDEO_TOKENS_PER_GEN = 48.0

PAYMENT_METHOD_LABELS: dict[str, str] = {
    "card_ru": "💳 Банковская карта (RU)",
    "sbp": "📱 СБП",
    "card_international": "🌍 Международная карта",
    "paypal": "🅿️ PayPal",
}


def _build_product_card_text(
    item: PaymentProductItem, current_index: int, total: int
) -> str:
    llm_generations = int(item.tokens_amount / LLM_TOKENS_PER_GEN)
    image_generations = int(item.tokens_amount / IMAGE_TOKENS_PER_GEN)
    video_generations = int(item.tokens_amount / VIDEO_TOKENS_PER_GEN)

    bonus_line = (
        "\n🎁 <b>Бонус:</b> VPN на 30 дней (при первом подключении)"
        if item.is_vpn_bonus_enabled
        else ""
    )
    description_line = f"\n📝 {item.description}" if item.description else ""

    return (
        "<b>Пополнение баланса 💳</b>\n"
        f"<blockquote>Тариф {current_index + 1} из {total}</blockquote>\n"
        f"<b>{item.name}</b>\n"
        f"🏷️ План: <b>{item.display_name}</b>\n"
        f"💸 Стоимость: <b>{item.price_rub:.0f} ₽</b>\n"
        f"🪙 Токены: <b>{item.tokens_amount:.0f}</b>\n"
        f"⏳ Длительность: <b>{item.duration_days} дней</b>\n"
        f"📆 Периодичность: <b>{'Ежемесячно' if item.billing_interval == 'monthly' else item.billing_interval}</b>"
        f"{description_line}"
        f"{bonus_line}\n\n"
        "<b>Примерные лимиты генераций</b>\n"
        f"• 💬 LLM: <b>до {llm_generations}</b>\n"
        f"• 🎨 Изображения: <b>до {image_generations}</b>\n"
        f"• 🎬 Видео: <b>до {video_generations}</b>"
    )


async def _load_products(
    callback: CallbackQuery,
    ai_service: AIService,
) -> list[PaymentProductItem] | None:
    if callback.from_user is None:
        await callback.answer("Не удалось определить пользователя", show_alert=True)
        return None

    tg_user_id = callback.from_user.id
    try:
        products_result = await ai_service.get_payment_products(tg_user_id=tg_user_id)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code in (401, 403):
            await callback.answer("Нет доступа к пополнению", show_alert=True)
        else:
            await callback.answer("Не удалось загрузить тарифы", show_alert=True)
        return None
    except Exception:
        logger.exception("Failed to load payment products for top-up")
        await callback.answer("Ошибка загрузки тарифов", show_alert=True)
        return None

    products = products_result.products
    if not products:
        await callback.answer("Тарифы пока недоступны", show_alert=True)
        return None
    return products


def _get_product_index_by_plan_id(
    products: list[PaymentProductItem],
    plan_id: str,
) -> int | None:
    for idx, item in enumerate(products):
        if str(item.plan_id) == plan_id:
            return idx
    return None


def _method_label(method_code: str) -> str:
    return PAYMENT_METHOD_LABELS.get(method_code, method_code)


async def _render_payment_methods_step(
    callback: CallbackQuery,
    ai_service: AIService,
    plan_index: int,
) -> None:
    products = await _load_products(callback, ai_service)
    if products is None:
        return

    plan_index = plan_index % len(products)
    selected = products[plan_index]

    try:
        methods_result = await ai_service.get_payment_methods(
            tg_user_id=callback.from_user.id
        )
    except httpx.HTTPStatusError:
        await callback.answer("Не удалось загрузить способы оплаты", show_alert=True)
        return
    except Exception:
        logger.exception("Failed to load payment methods for top-up")
        await callback.answer("Ошибка загрузки способов оплаты", show_alert=True)
        return

    methods = [
        (item.code, _method_label(item.code))
        for item in methods_result.methods
        if item.enabled and not item.is_soon
    ]
    if not methods:
        await callback.answer("Доступных способов оплаты пока нет", show_alert=True)
        return

    text = (
        "<b>Выбор способа оплаты 💳</b>\n"
        f"Тариф: <b>{selected.name}</b>\n"
        f"Стоимость: <b>{selected.price_rub:.0f} ₽</b>\n\n"
        "Выбери удобный способ оплаты:"
    )

    if callback.message is not None:
        await callback.message.edit_text(
            text,
            reply_markup=build_payment_methods_keyboard(methods, plan_index),
        )
    await callback.answer()


@router.message(F.text == BALANCE_BUTTON_TEXT)
async def show_balance(
    message: Message,
    ai_service: FromDishka[AIService],
) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя. Попробуй еще раз.")
        return

    tg_user_id = message.from_user.id

    try:
        balance = await ai_service.get_user_balance(tg_user_id=tg_user_id)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 401:
            await message.answer(
                "Сервис сейчас временно недоступен. Попробуй чуть позже."
            )
        elif status_code == 404:
            await message.answer("Профиль пользователя не найден.")
        else:
            await message.answer("Не удалось получить баланс. Попробуй позже.")
        return
    except Exception:
        logger.exception("Failed to load user balance")
        await message.answer("Не удалось загрузить баланс. Попробуй позже.")
        return

    text = (
        "<b>Баланс аккаунта 💰</b>\n"
        f"<blockquote>{balance.available_tokens:.4f} токенов доступно</blockquote>\n"
        f"В холде: <b>{balance.hold_tokens:.4f}</b>\n\n"
        "Чтобы продолжить генерации без пауз, держи небольшой запас токенов."
    )

    await message.answer(text, reply_markup=build_balance_keyboard())


@router.callback_query(F.data == "balance:top_up")
async def top_up_balance(
    callback: CallbackQuery,
    ai_service: FromDishka[AIService],
) -> None:
    products = await _load_products(callback, ai_service)
    if products is None:
        return
    current_index = 0
    current_item = products[current_index]
    text = _build_product_card_text(current_item, current_index, len(products))

    if callback.message is not None:
        await callback.message.answer(
            text,
            reply_markup=build_balance_products_keyboard(products, current_index),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("balance:product:select:"))
async def select_balance_product(
    callback: CallbackQuery,
    ai_service: FromDishka[AIService],
) -> None:
    products = await _load_products(callback, ai_service)
    if products is None:
        return

    plan_id = (callback.data or "").split(":")[-1]
    plan_index = _get_product_index_by_plan_id(products, plan_id)
    if plan_index is None:
        await callback.answer("Тариф не найден", show_alert=True)
        return
    await _render_payment_methods_step(callback, ai_service, plan_index)


@router.callback_query(F.data.startswith("balance:method:back:"))
async def back_to_methods(
    callback: CallbackQuery,
    ai_service: FromDishka[AIService],
) -> None:
    try:
        plan_index = int((callback.data or "").split(":")[-1])
    except ValueError:
        await callback.answer("Не удалось вернуться к способам оплаты", show_alert=True)
        return
    await _render_payment_methods_step(callback, ai_service, plan_index)


@router.callback_query(F.data.startswith("balance:method:pick:"))
async def pick_payment_method(
    callback: CallbackQuery,
    ai_service: FromDishka[AIService],
) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) < 5:
        await callback.answer("Некорректный способ оплаты", show_alert=True)
        return

    try:
        plan_index = int(parts[3])
    except ValueError:
        await callback.answer("Некорректный тариф", show_alert=True)
        return
    payment_method = parts[4]

    products = await _load_products(callback, ai_service)
    if products is None:
        return

    if not (0 <= plan_index < len(products)):
        await callback.answer("Тариф не найден", show_alert=True)
        return
    selected = products[plan_index]

    text = (
        "<b>Подтверждение пополнения 💳</b>\n"
        f"Выбранный план: <b>{selected.name}</b>\n"
        f"Стоимость: <b>{selected.price_rub:.0f} ₽</b>\n"
        f"Токены: <b>{selected.tokens_amount:.0f}</b>\n"
        f"Длительность: <b>{selected.duration_days} дней</b>\n"
        f"Способ оплаты: <b>{_method_label(payment_method)}</b>\n\n"
        "Нажми <b>Оплатить</b>, чтобы создать инвойс."
    )

    if callback.message is not None:
        await callback.message.edit_text(
            text,
            reply_markup=build_balance_checkout_keyboard(plan_index, payment_method),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("balance:pay:"))
async def pay_selected_plan(
    callback: CallbackQuery,
    ai_service: FromDishka[AIService],
) -> None:
    if callback.from_user is None:
        await callback.answer("Не удалось определить пользователя", show_alert=True)
        return

    parts = (callback.data or "").split(":")
    if len(parts) < 4:
        await callback.answer("Некорректные параметры оплаты", show_alert=True)
        return

    try:
        plan_index = int(parts[2])
    except ValueError:
        await callback.answer("Некорректный тариф", show_alert=True)
        return
    payment_method = parts[3]

    products = await _load_products(callback, ai_service)
    if products is None:
        return
    if not (0 <= plan_index < len(products)):
        await callback.answer("Тариф не найден", show_alert=True)
        return
    plan_id = str(products[plan_index].plan_id)

    try:
        invoice = await ai_service.create_invoice(
            tg_user_id=callback.from_user.id,
            plan_id=plan_id,
            payment_method=payment_method,
        )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code in (401, 403):
            await callback.answer("Нет доступа к оплате", show_alert=True)
        elif status_code == 400:
            await callback.answer(
                "Не удалось создать инвойс для этого тарифа", show_alert=True
            )
        else:
            await callback.answer("Ошибка при создании инвойса", show_alert=True)
        return
    except Exception:
        logger.exception("Failed to create invoice from bot")
        await callback.answer("Временная ошибка при создании платежа", show_alert=True)
        return

    if callback.message is not None:
        if invoice.payment_url:
            await callback.message.answer(
                "<b>Инвойс создан ✅</b>\n"
                f"Сумма: <b>{invoice.amount:.0f} ₽</b>\n"
                "Нажми кнопку ниже, чтобы перейти к оплате.",
                reply_markup=build_balance_payment_link_keyboard(invoice.payment_url),
            )
        else:
            await callback.message.answer(
                "<b>Инвойс создан ✅</b>\n"
                "Платежная ссылка временно недоступна. Попробуй еще раз.",
            )
    await callback.answer()


@router.callback_query(F.data.startswith("balance:product:nav:"))
async def navigate_balance_products(
    callback: CallbackQuery,
    ai_service: FromDishka[AIService],
) -> None:
    products = await _load_products(callback, ai_service)
    if products is None:
        return

    try:
        current_index = int((callback.data or "").split(":")[-1])
    except ValueError:
        await callback.answer("Не удалось переключить тариф", show_alert=True)
        return

    total = len(products)
    current_index = current_index % total
    current_item = products[current_index]
    text = _build_product_card_text(current_item, current_index, total)

    if callback.message is not None:
        await callback.message.edit_text(
            text,
            reply_markup=build_balance_products_keyboard(products, current_index),
        )
    await callback.answer()


@router.callback_query(F.data == "balance:product:noop")
async def noop_balance_product(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data == "balance:back")
async def back_to_balance(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.answer(
            "<b>Баланс аккаунта 💰</b>\nВыбери действие:",
            reply_markup=build_balance_keyboard(),
        )
    await callback.answer()


@router.message(F.text == REFERRAL_BUTTON_TEXT)
async def referral_program_info(message: Message) -> None:
    await message.answer(
        "<b>Реферальная программа 🎁</b>\n"
        "Скоро запустим бонусы за приглашения. Следи за обновлениями ✨"
    )
