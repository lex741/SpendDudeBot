# handlers/balance.py

from aiogram.types import Message
from bot_config import dp
from db.database import SessionLocal
from db.models import User

# заглушка, потом заменим на запрос к БД
def get_user_balance(user_id: int) -> float:
    db = SessionLocal()
    user = db.query(User).get(user_id)
    if not user:
        user = User(user_id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()
    return user.balance

@dp.message(lambda message: message.text == "💰 Баланс")
async def cmd_balance(message: Message):
    balance = get_user_balance(message.from_user.id)
    await message.answer(f"Ваш текущий баланс: {balance}")
@dp.message(lambda message: message.text == "💰 Баланс")
async def cmd_balance(message: Message):
    print("BALANCE handler fired:", message.text)   # это в консоль PyCharm
    balance = get_user_balance(message.from_user.id)
    await message.answer(f"Ваш текущий баланс: {balance}")