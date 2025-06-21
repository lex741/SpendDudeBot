# bot_config.py
from dotenv import load_dotenv
import os

from aiogram import Bot, Dispatcher

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()    # убрал лишний '+'
