import re
import datetime
from zoneinfo import ZoneInfo
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile,
    ReplyKeyboardRemove,
)
from bot_config import dp, bot
from services.expenses import get_expenses_filtered
from services.categories import get_category_by_id
from utils.buttons import main_kb
import csv
import os

# состояние для custom диапазона
export_state: dict[int, bool] = {}

@dp.message(lambda m: m.text == "📤 Экспорт")
async def export_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="За месяц", callback_data="export_month"),
        InlineKeyboardButton(text="За год",    callback_data="export_year"),
        InlineKeyboardButton(text="Свои даты", callback_data="export_custom"),
    ]])
    await message.answer("Выберите период для экспорта CSV:", reply_markup=kb)

@dp.callback_query(lambda c: c.data in ("export_month", "export_year"))
async def export_standard_period(query: CallbackQuery):
    user_id = query.from_user.id
    now = datetime.datetime.now(tz=ZoneInfo("Europe/Kyiv"))
    tag = query.data.split("_")[1]
    if tag == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    end = now
    await generate_and_send_csv(user_id, start, end, query.message)
    await query.answer()

@dp.callback_query(lambda c: c.data == "export_custom")
async def export_custom(query: CallbackQuery):
    export_state[query.from_user.id] = True
    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.answer(
        "Введите диапазон YYYY-MM-DD–YYYY-MM-DD для экспорта:",
        reply_markup=ReplyKeyboardRemove()
    )
    await query.answer()

@dp.message(lambda m: export_state.get(m.from_user.id))
async def export_custom_input(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})[–-](\d{4}-\d{2}-\d{2})", text)
    if not m:
        return await message.answer("Неверный формат. Пример: 2025-06-01–2025-06-30", reply_markup=main_kb)
    start = datetime.datetime.fromisoformat(m.group(1)).replace(tzinfo=ZoneInfo("Europe/Kyiv"))
    end   = datetime.datetime.fromisoformat(m.group(2)).replace(tzinfo=ZoneInfo("Europe/Kyiv"))
    await generate_and_send_csv(user_id, start, end, message)
    export_state.pop(user_id, None)

async def generate_and_send_csv(user_id: int, start: datetime.datetime, end: datetime.datetime, target):
    # получаем траты
    exps = get_expenses_filtered(user_id, start=start, end=end)
    if not exps:
        return await target.answer("Нет трат за указанный период.", reply_markup=main_kb)
    # готовим файл
    filename = f"export_{user_id}.csv"
    # группируем по категориям
    from itertools import groupby
    # Сортируем по имени категории
    exps_sorted = sorted(exps, key=lambda e: get_category_by_id(e.category_id).name)
    with open(filename, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        # Для каждой категории выводим заголовок и под ним строки
        for cat_name, items in groupby(exps_sorted, key=lambda e: get_category_by_id(e.category_id).name):
            writer.writerow([f"Категория: {cat_name}"])
            # Заголовки столбцов: дата, сумма, комментарий
            writer.writerow(["Дата", "Сумма", "Комментарий"])
            for e in items:
                date_str = e.date.astimezone(ZoneInfo("Europe/Kyiv")).strftime("%Y-%m-%d %H:%M")
                writer.writerow([date_str, f"{e.amount:.2f}", e.comment or ""])
            # пустая строка для разделения
            writer.writerow([])
    # отправляем файл
    file = FSInputFile(filename)
    await bot.send_document(chat_id=user_id, document=file, reply_markup=main_kb)
    # удаляем временный файл
    os.remove(filename)
