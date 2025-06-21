# utils/buttons.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

btn_expense    = KeyboardButton(text="➕ Добавить трату")
btn_balance    = KeyboardButton(text="💰 Баланс")
btn_history    = KeyboardButton(text="📜 История")
btn_categories = KeyboardButton(text="📂 Категории")
btn_analytics  = KeyboardButton(text="📊 Аналитика")
btn_export     = KeyboardButton(text="📤 Экспорт")
btn_share      = KeyboardButton(text="👥 Совместный бюджет")

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [btn_expense, btn_balance],
        [btn_history, btn_categories],
        [btn_analytics, btn_export],
        [btn_share],
    ],
    resize_keyboard=True
)
