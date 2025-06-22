import re
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    ReplyKeyboardRemove
)
from bot_config import dp
from services.expenses import get_user_balance, set_user_balance
from utils.buttons import main_kb

# state при ручной установке баланса
user_balance_state: dict[int, str] = {}

@dp.message(lambda m: m.text == "💰 Баланс")
async def show_balance(message: Message):
    balance = get_user_balance(message.from_user.id)
    text = f"Ваш текущий баланс: {balance:.2f} ₴"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⚙️ Установить баланс", callback_data="balance_set")
    ]])
    await message.answer(text, reply_markup=kb)

@dp.callback_query(lambda c: c.data == "balance_set")
async def balance_set_request(query: CallbackQuery):
    user_balance_state[query.from_user.id] = "setting"
    # убираем кнопку
    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.answer(
        "Введите новую сумму баланса:",
        reply_markup=ReplyKeyboardRemove()
    )
    await query.answer()

@dp.message(lambda m: user_balance_state.get(m.from_user.id) == "setting")
async def balance_set_apply(message: Message):
    try:
        amount = float(message.text.replace(',', '.'))
    except ValueError:
        return await message.answer(
            "Неверный формат. Введите число, например 1500.00:"
        )
    set_user_balance(message.from_user.id, amount)
    await message.answer(
        f"Баланс установлен: {amount:.2f} ₴",
        reply_markup=main_kb
    )
    user_balance_state.pop(message.from_user.id, None)
