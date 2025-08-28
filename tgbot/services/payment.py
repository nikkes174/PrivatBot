import hashlib
import logging
import os
import urllib.parse
from typing import Dict

from aiogram import types
from dotenv import load_dotenv

load_dotenv()

MERCHANT_LOGIN = os.getenv("ROBO_LOGIN")

PASSWORD1 = os.getenv("ROBO_PASS1")


IS_TEST = "0"

ROBO_URL = "https://auth.robokassa.ru/Merchant/Index.aspx"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class PaymentService:
    """Класс для формирования платёжных ссылок через Robokassa."""

    def __init__(
        self, merchant_login: str = MERCHANT_LOGIN, password1: str = PASSWORD1
    ):
        self.merchant_login = merchant_login
        self.password1 = password1
        self.pending_payments: Dict[str, int] = {}

    def _generate_signature(
        self, out_sum: str, inv_id: str, shp_params: Dict[str, str]
    ) -> str:
        """Формирует подпись MD5 для Robokassa."""
        shp_str = ":".join(f"{k}={v}" for k, v in sorted(shp_params.items()))
        string_for_sign = (
            f"{self.merchant_login}:{out_sum}:{inv_id}:"
            f"{self.password1}:{shp_str}"
        )
        return hashlib.md5(string_for_sign.encode("utf-8")).hexdigest().upper()

    def generate_payment_url(
        self, user_id: int, months: int, price: int
    ) -> str:
        """Генерирует платёжную ссылку Robokassa."""
        out_sum = f"{price}.00"
        inv_id = str(user_id * 10 + months)
        description = f"Подписка на {months} мес."
        shp_params = {"Shp_months": str(months), "Shp_user": str(user_id)}
        signature_value = self._generate_signature(out_sum, inv_id, shp_params)
        params = {
            "MerchantLogin": self.merchant_login,
            "OutSum": out_sum,
            "InvId": inv_id,
            "Description": description,
            "SignatureValue": signature_value,
            "IsTest": IS_TEST,
            **shp_params,
        }
        return f"{ROBO_URL}?{urllib.parse.urlencode(params)}"

    async def start_payment(
        self, callback_query: types.CallbackQuery, months: int, price: int
    ) -> None:
        """
        Запускает процесс оплаты:
        - генерирует ссылку
        - сохраняет в pending_payments
        - отправляет пользователю
        """
        user_id = callback_query.from_user.id
        payment_url = self.generate_payment_url(user_id, months, price)
        inv_id = str(user_id * 10 + months)
        self.pending_payments[inv_id] = user_id
        logging.info(
            "💰 Новый платёж: user_id=%s, months=%s, amount=%s",
            user_id,
            months,
            price,
        )

        await callback_query.message.answer(
            f"Для оплаты подписки на {months} мес. нажмите 👉 "
            f'<a href="{payment_url}">Оплатить</a>',
            parse_mode="HTML",
        )
        await callback_query.answer()
