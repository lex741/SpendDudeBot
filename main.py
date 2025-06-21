import asyncio
import os
from dotenv import load_dotenv
from bot_config import bot, dp
import handlers.balance   # noqa: F401
from aiogram.types import Message
from aiogram.filters import Command
from utils.buttons import main_kb
from db.database import engine
from db.models import Base
import handlers.categories
import handlers.expenses

Base.metadata.create_all(bind=engine)
# 3) Теперь единственный dp, с которым работаем мы и хендлеры
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Выбери действие:",
        reply_markup=main_kb
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Список команд:\n"
        "/start — меню\n"
        "/help — справка",
        reply_markup=main_kb
    )

async def main():
    # стартуем именно тот dp, на который подписаны все модули
    await dp.start_polling(bot)

if __name__ == "__main__":
    load_dotenv()  # убедиться, что токен подгружен
    asyncio.run(main())
