# handlers/balance.py

from aiogram.types import Message
from bot_config import dp
from db.database import SessionLocal
from db.models import User
from services.expenses import get_user_balance


@dp.message(lambda message: message.text == "💰 Баланс")
async def cmd_balance(message: Message):
    balance = get_user_balance(message.from_user.id)
    await message.answer(f"Ваш текущий баланс: {balance}")
@dp.message(lambda message: message.text == "💰 Баланс")
async def cmd_balance(message: Message):
    print("BALANCE handler fired:", message.text)   # это в консоль PyCharm
    balance = get_user_balance(message.from_user.id)
    await message.answer(f"Ваш текущий баланс: {balance}")