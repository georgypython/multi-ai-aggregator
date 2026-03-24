from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka
import httpx

from src.core.logger import logger
from src.keyboards.ai import (
    BALANCE_BUTTON_TEXT,
    REFERRAL_BUTTON_TEXT,
    build_balance_keyboard,
)
from src.services.ai import AIService

router = Router()


@router.message(F.text == BALANCE_BUTTON_TEXT)
async def show_balance(
    message: Message,
    ai_service: FromDishka[AIService],
) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить Telegram пользователя")
        return

    tg_user_id = message.from_user.id

    try:
        balance = await ai_service.get_user_balance(user_id=str(tg_user_id))
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 401:
            await message.answer("Ошибка авторизации бота на backend.")
        elif status_code == 404:
            await message.answer("Профиль пользователя не найден.")
        else:
            await message.answer(f"Не удалось получить баланс: HTTP {status_code}")
        return
    except Exception:
        logger.exception("Failed to load user balance")
        await message.answer("Не удалось загрузить баланс. Попробуй позже.")
        return

    text = (
        "<b>💰 Баланс</b>\n"
        f"<blockquote>{balance.available_tokens:.4f} токенов</blockquote>\n"
        "Пополните баланс по кнопке ниже 👇"
    )

    await message.answer(text, reply_markup=build_balance_keyboard())


@router.callback_query(F.data == "balance:top_up")
async def top_up_balance(callback: CallbackQuery) -> None:
    await callback.answer("Пополнение скоро будет доступно", show_alert=True)


@router.message(F.text == REFERRAL_BUTTON_TEXT)
async def referral_program_info(message: Message) -> None:
    await message.answer("Реферальная программа скоро будет доступна.")
