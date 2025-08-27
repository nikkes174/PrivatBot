import urllib.parse
from unittest.mock import AsyncMock

import pytest
from tgbot.services.payment import PaymentService

service = PaymentService(merchant_login="test_login", password1="test_pass")

user_id = 123

months = 3

price = 500


def test_generate_payment_url():
    url = service.generate_payment_url(user_id, months, price)
    params = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
    assert params["MerchantLogin"] == "test_login"
    assert params["OutSum"] == "500.00"
    assert params["InvId"] == str(user_id * 10 + months)
    assert params["Shp_user"] == str(user_id)
    assert params["Shp_months"] == str(months)
    assert len(params["SignatureValue"]) == 32


@pytest.mark.parametrize("out_sum, inv_id, shp_params", [
    ("100.00", "1", {"Shp_user": "123"}),
    ("200.00", "2", {"Shp_user": "456"}),
    ("300.00", "3", {"Shp_user": "789"}),
])
def test_signature_length_and_type(out_sum, inv_id, shp_params):
    signature = service._generate_signature(out_sum, inv_id, shp_params)
    assert isinstance(signature, str)
    assert len(signature) == 32


@pytest.mark.asyncio
async def test_start_payment():
    callback_query = AsyncMock()
    callback_query.from_user.id = 123
    callback_query.message.answer = AsyncMock()
    callback_query.answer = AsyncMock()

    await service.start_payment(callback_query, months, price)

    inv_id = str(123 * 10 + months)

    assert inv_id in service.pending_payments
    assert service.pending_payments[inv_id] == 123

    callback_query.message.answer.assert_awaited_once()
    args, kwargs = callback_query.message.answer.call_args

    assert "Оплатить" in args[0]
    callback_query.answer.assert_awaited_once()


