from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import TARIFF_PRICES
from tgbot.services.payment import PaymentService


def first_start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="️‍️‍️‍️‍️‍️‍️‍✅ Подписки", callback_data="to_rate")
    builder.button(
        text="📊 Ознакомление с офертой",
        url="https://telegra.ph/"
        "Dogovor-ofertypolzovatelskoe-soglashenie-s-klientom-08-07",
    )
    builder.adjust(1)
    return builder.as_markup()


def chane_sub():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="️‍️‍️‍️‍️‍️‍️‍✅ Отменить автопродление",
        callback_data="to_change",
    )
    builder.adjust(1)
    return builder.as_markup()


def to_back():
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад 🔙️", callback_data="back_to")
    builder.adjust(1, 1)
    return builder.as_markup()


def to_access():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔒 Войти в закрытый канал", url="https://t.me/+-E8hgZJHuaQ1NzVi"
    )
    builder.adjust(1, 1)
    return builder.as_markup()


def tariffs_keyboard(user_id: int) -> InlineKeyboardMarkup:
    payment_service = PaymentService()
    buttons = [
        [
            InlineKeyboardButton(
                text="🔥 1 месяц",
                url=payment_service.generate_payment_url(
                    user_id, 1, TARIFF_PRICES[1]
                ),
            )
        ],
        [
            InlineKeyboardButton(
                text="⚡️ 3 месяца",
                url=payment_service.generate_payment_url(
                    user_id, 3, TARIFF_PRICES[3]
                ),
            )
        ],
        [
            InlineKeyboardButton(
                text="🖤 6 месяцев",
                url=payment_service.generate_payment_url(
                    user_id, 6, TARIFF_PRICES[6]
                ),
            )
        ],
        [
            InlineKeyboardButton(
                text="🐘 9 месяцев",
                url=payment_service.generate_payment_url(
                    user_id, 9, TARIFF_PRICES[9]
                ),
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
