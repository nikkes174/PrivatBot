import asyncio
import logging
import pytz
import asyncpg
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot
import os
from typing import Optional


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_ID = os.getenv("CHANNEL_ID")

DB_DSN = os.getenv("DB_DSN")

bot = Bot(BOT_TOKEN)

MoscowTimeZone = pytz.timezone("Europe/Moscow")

TARIFF_PRICES = {
    1: 1290,
    3: 3490,
    6: 6490,
    9: 8990,
}


async def add_subscription(
    user_id: int,
    user_name: str,
    months: int,
    recurring_id: Optional[str] = None,
) -> None:
    """
    Создаёт или обновляет подписку в БД.
    """
    conn = await asyncpg.connect(DB_DSN)
    try:
        start_date = date.today()
        end_date = start_date + timedelta(days=30 * months)

        await conn.execute(
            """
            INSERT INTO public.privat_user 
            (user_id, user_name, start_subscription, end_subscription, duration_months, recurring_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id) DO UPDATE
            SET start_subscription = EXCLUDED.start_subscription,
                end_subscription = EXCLUDED.end_subscription,
                duration_months = EXCLUDED.duration_months,
                recurring_id = EXCLUDED.recurring_id,
                user_name = EXCLUDED.user_name
            """,
            user_id,
            user_name,
            start_date,
            end_date,
            months,
            recurring_id,
        )
        logging.info("✅ Подписка для user_id=%s обновлена/создана", user_id)
    except Exception as e:
        logging.error("❌ Ошибка при добавлении подписки: %s", e)
    finally:
        await conn.close()


async def charge_recurring_payment(recurring_id: str, amount: int) -> str:
    """
    Заглушка для рекуррентного платежа.
    Здесь нужно вызвать реальный API Робокассы.
    """
    logging.info("⚡ Платёж по recurring_id=%s на сумму %s", recurring_id, amount)
    # TODO: реализовать реальный запрос к API Робокассы
    return "OK"


async def check_subscriptions() -> None:
    """
    Проверяет подписки пользователей и продлевает их,
    отключает при отсутствии оплаты.
    """
    conn = await asyncpg.connect(DB_DSN)
    try:
        today = date.today()

        rows = await conn.fetch(
            """
            SELECT user_id, duration_months, recurring_id 
            FROM public.privat_user 
            WHERE end_subscription < $1
            """,
            today,
        )

        for row in rows:
            user_id = row["user_id"]
            months = row["duration_months"]
            recurring_id = row["recurring_id"]

            if recurring_id:
                amount = TARIFF_PRICES.get(months, 1290)
                result = await charge_recurring_payment(recurring_id, amount)

                if "OK" in result:
                    new_end = today + timedelta(days=30 * months)
                    await conn.execute(
                        """
                        UPDATE public.privat_user 
                        SET start_subscription=$1, end_subscription=$2 
                        WHERE user_id=$3
                        """,
                        today,
                        new_end,
                        user_id,
                    )
                    await bot.send_message(
                        user_id, "✅ Подписка автоматически продлена. Спасибо, что остаетесь с нами!"
                    )
                    logging.info("🔄 Продлена подписка для user_id=%s", user_id)
                else:
                    await _remove_user(conn, user_id, "❌ Автоплатёж не прошёл, подписка завершена.")
            else:
                await _remove_user(conn, user_id, "❌ Срок подписки истёк, доступ закрыт.")

    except Exception as e:
        logging.error("❌ Ошибка при проверке подписок: %s", e)
    finally:
        await conn.close()


async def _remove_user(conn, user_id: int, message: str) -> None:
    """Удаляет пользователя из БД и блокирует доступ в канал."""
    try:
        await bot.ban_chat_member(CHANNEL_ID, user_id)
        await bot.unban_chat_member(CHANNEL_ID, user_id)  # «кик» пользователя
        await conn.execute("DELETE FROM public.privat_user WHERE user_id=$1", user_id)
        await bot.send_message(user_id, message)
        logging.info("❌ Удалён user_id=%s (причина: %s)", user_id, message)
    except Exception as e:
        logging.error("⚠️ Ошибка при удалении пользователя %s: %s", user_id, e)


async def scheduler() -> None:
    """
    Планировщик: проверяет подписки каждый день в 08:00 по МСК.
    """
    logging.info("📅 Планировщик запущен (ожидание 08:00 по МСК)")

    while True:
        now = datetime.now(MoscowTimeZone)

        if now.hour == 8 and now.minute == 0:
            logging.info("🔄 Запуск проверки подписок...")
            try:
                await check_subscriptions()
                logging.info("✅ Проверка подписок завершена успешно")
            except Exception as e:
                logging.error("❌ Ошибка в check_subscriptions: %s", e)
            await asyncio.sleep(60)  # чтобы не зациклиться

        await asyncio.sleep(30)
