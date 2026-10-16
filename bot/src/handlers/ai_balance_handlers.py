from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka
import httpx

from src.core.config import settings
from src.core.logger import logger
from src.keyboards.ai import (
    BALANCE_BUTTON_TEXT,
    REFERRAL_BUTTON_TEXT,
    build_balance_keyboard,
    build_balance_payment_link_keyboard,
)
from src.services.ai import AIService

router = Router()


async def _show_miniapp_top_up(callback: CallbackQuery) -> None:
    miniapp_url = settings.app.miniapp_url.strip()
    if not miniapp_url:
        await callback.answer("Ссылка Mini App не настроена", show_alert=True)
        return

    if callback.message is not None:
        await callback.message.answer(
            "<b>Пополнение баланса 💳</b>\nОткрой Mini App и заверши оплату там.",
            reply_markup=build_balance_payment_link_keyboard(miniapp_url),
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

    await message.answer(
        text,
        reply_markup=build_balance_keyboard(settings.app.miniapp_url),
    )


@router.callback_query(F.data == "balance:top_up")
async def top_up_balance(
    callback: CallbackQuery,
) -> None:
    await _show_miniapp_top_up(callback)


@router.callback_query(F.data.startswith("balance:product:select:"))
async def select_balance_product(
    callback: CallbackQuery,
) -> None:
    await _show_miniapp_top_up(callback)


@router.callback_query(F.data.startswith("balance:method:back:"))
async def back_to_methods(
    callback: CallbackQuery,
) -> None:
    await _show_miniapp_top_up(callback)


@router.callback_query(F.data.startswith("balance:method:pick:"))
async def pick_payment_method(
    callback: CallbackQuery,
) -> None:
    await _show_miniapp_top_up(callback)


@router.callback_query(F.data.startswith("balance:pay:"))
async def pay_selected_plan(
    callback: CallbackQuery,
) -> None:
    await _show_miniapp_top_up(callback)


@router.callback_query(F.data.startswith("balance:product:nav:"))
async def navigate_balance_products(
    callback: CallbackQuery,
) -> None:
    await _show_miniapp_top_up(callback)


@router.callback_query(F.data == "balance:product:noop")
async def noop_balance_product(callback: CallbackQuery) -> None:
    await _show_miniapp_top_up(callback)


@router.callback_query(F.data == "balance:back")
async def back_to_balance(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.answer(
            "<b>Баланс аккаунта 💰</b>\nВыбери действие:",
            reply_markup=build_balance_keyboard(settings.app.miniapp_url),
        )
    await callback.answer()


@router.message(F.text == REFERRAL_BUTTON_TEXT)
async def referral_program_info(message: Message) -> None:
    await message.answer(
        "<b>Реферальная программа 🎁</b>\n"
        "Скоро запустим бонусы за приглашения. Следи за обновлениями ✨"
    )
