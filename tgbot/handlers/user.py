import hashlib
import logging
import os
import time

import aiohttp
import asyncpg
from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, FSInputFile
from dotenv import load_dotenv

from tgbot.keyboards.inline import first_start_keyboard, tariffs_keyboard

load_dotenv()

user_router = Router()

MERCHANT_LOGIN = os.getenv("ROBO_LOGIN")

PASSWORD1 = os.getenv("ROBO_PASS1")

DB = os.getenv("DATABASE_URL")

logging.basicConfig(level=logging.INFO)


@user_router.message(CommandStart())
async def user_start(message: types.Message) -> None:
    """Приветственное сообщение при старте."""
    try:
        photo = FSInputFile("путь до файла на сервере")
    except Exception:
        photo = None

    caption_text = (
        "Смешная сумма за результат:"
        " 43₽ в день — дешевле, чем проезд в метро!\n"
        "1 290₽/мес — вложение, которое окупится уже через неделю!\n\n"
        "📌 РЕАЛЬНОСТЬ:\n"
        "✔️ Выход из матрицы и контроль своей жизни\n"
        "✔️ Успех среди женщин и уважение среди мужчин\n"
        "✔️ Сильное окружение — твой надёжный тыл\n\n"
        "Это не просто приватный канал — это трамплин в новую реальность 😎"
    )

    if photo:
        await message.answer_photo(photo=photo, caption=caption_text)
    else:
        await message.answer(caption_text)

    await message.answer(
        "Перед покупкой не забудь ознакомиться с офертой 👇🏻",
        reply_markup=first_start_keyboard(),
    )


@user_router.callback_query(F.data == "to_rate")
async def show_tariffs(call: CallbackQuery) -> None:
    """Меню с тарифами (кнопки → Robokassa)."""
    kb = tariffs_keyboard(call.from_user.id)

    await call.message.edit_text(
        text=(
            "👇🏻 ВЫБИРАЙ ТАРИФ И МЕНЯЙ СВОЮ ЖИЗНЬ:\n\n"
            "➡️ 1 месяц — 1 290 ₽\n"
            "➡️ 3 месяца — 3 490 ₽ (скидка 10%)\n"
            "➡️ 6 месяцев — 6 490 ₽ (скидка 15%)\n"
            "➡️ 9 месяцев — 8 990 ₽ (скидка 20%)"
        ),
        reply_markup=kb,
    )


async def charge_recurring_payment(recurring_id: str, amount: int) -> str:
    """Вызывает Robokassa API для рекуррентного платежа."""
    invoice_id = int(time.time())
    out_sum = f"{amount:.2f}"

    signature_str = (
        f"{MERCHANT_LOGIN}:{out_sum}:{invoice_id}:{recurring_id}:{PASSWORD1}"
    )
    signature = hashlib.md5(signature_str.encode()).hexdigest()

    payload = {
        "MerchantLogin": MERCHANT_LOGIN,
        "OutSum": out_sum,
        "InvoiceID": invoice_id,
        "RecurringId": recurring_id,
        "Description": "Продление подписки",
        "SignatureValue": signature,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://auth.robokassa.ru/Merchant/Recurring", data=payload
        ) as resp:
            text = await resp.text()
            logging.info("⚡ Recurring payment: %s", text)
            return text


@user_router.callback_query(F.data == "to_change")
async def cancel_subscription(call: CallbackQuery) -> None:
    """Отмена подписки (очистка recurring_id в БД)."""
    user_id = call.from_user.id

    try:
        conn = await asyncpg.connect(DB)
        await conn.execute(
            "UPDATE public.privat_user "
            "SET recurring_id = NULL WHERE user_id = $1",
            user_id,
        )
        await conn.close()
        logging.info("🔴 Подписка отменена для user_id=%s", user_id)
        await call.message.edit_text("🔴 Ваша подписка была отменена.")
    except Exception as e:
        logging.error("❌ Ошибка при отмене подписки: %s", e)
        await call.message.edit_text(
            "⚠️ Не удалось отменить подписку, попробуйте позже."
        )

    await call.answer()
