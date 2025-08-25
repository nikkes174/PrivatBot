import os
import hashlib
import logging
import asyncpg
from datetime import date, timedelta
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from aiogram import Bot
from tgbot.keyboards.inline import chane_sub

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

DB_DSN = os.getenv("DB_DSN")

ROBO_PASS1 = os.getenv("ROBO_PASS1")

ROBO_PASS2 = os.getenv("ROBO_PASS2")

bot = Bot(BOT_TOKEN)
app = FastAPI()

logging.basicConfig(level=logging.INFO)

def generate_signature(*parts: str) -> str:
    raw_str = ":".join(parts)
    return hashlib.md5(raw_str.encode("utf-8")).hexdigest().upper()

@app.get("/robokassa/result")
async def robokassa_result(
    OutSum: str,
    InvId: str,
    Shp_user: str,
    Shp_months: str,
    SignatureValue: str
):
    """Callback от Robokassa после оплаты (обновление подписки в БД)."""

    my_crc = generate_signature(OutSum, InvId, ROBO_PASS2,
                                f"Shp_months={Shp_months}", f"Shp_user={Shp_user}")

    if my_crc != SignatureValue.upper():
        logging.error("❌ Bad sign for InvId=%s", InvId)
        return PlainTextResponse("bad sign", status_code=400)

    user_id = int(Shp_user)
    months = int(Shp_months)
    user_name = f"user_{user_id}"
    recurring_id = InvId

    start_date = date.today()
    end_date = start_date + timedelta(days=30 * months)

    conn = await asyncpg.connect(DB_DSN)
    try:
        await conn.execute("""
            INSERT INTO public.privat_user (user_id, user_name, start_subscription, end_subscription, duration_months, recurring_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id) DO UPDATE
            SET start_subscription = EXCLUDED.start_subscription,
                end_subscription = EXCLUDED.end_subscription,
                duration_months = EXCLUDED.duration_months,
                recurring_id = EXCLUDED.recurring_id,
                user_name = EXCLUDED.user_name
        """, user_id, user_name, start_date, end_date, months, recurring_id)
    finally:
        await conn.close()

    logging.info("✅ Оплата подтверждена: user_id=%s, months=%s", user_id, months)
    return PlainTextResponse(f"OK{InvId}")

@app.get("/robokassa/success")
async def robokassa_success(
    OutSum: str,
    InvId: str,
    Shp_user: str,
    Shp_months: str,
    SignatureValue: str
):
    """Успешная оплата (видно в браузере клиента)."""

    my_crc = generate_signature(OutSum, InvId, ROBO_PASS1,
                                f"Shp_months={Shp_months}", f"Shp_user={Shp_user}")

    if my_crc.lower() != SignatureValue.lower():
        logging.error("❌ Bad success sign for InvId=%s", InvId)
        return PlainTextResponse("bad sign", status_code=400)

    user_id = int(Shp_user)

    invite_link = await bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        expire_date=None,
        member_limit=1,
        name=f"Оплата InvId={InvId}"
    )

    await bot.send_message(
        user_id,
        f"✅ Оплата прошла успешно!\n"
        f"Вот доступ в закрытый канал:\n{invite_link.invite_link}",
        reply_markup=chane_sub()
    )

    logging.info("🔑 Invite link создан для user_id=%s", user_id)
    return PlainTextResponse("Оплата прошла успешно. Вернись в Telegram 😉")

@app.get("/robokassa/fail")
async def robokassa_fail(request: Request):
    """Ошибка/отмена оплаты."""
    logging.warning("❌ Пользователь отменил оплату: %s", request.query_params)
    return PlainTextResponse("Оплата не прошла ❌")
