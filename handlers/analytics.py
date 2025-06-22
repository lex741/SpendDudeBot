import datetime
from zoneinfo import ZoneInfo
import re
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
    ReplyKeyboardRemove,
)
from bot_config import dp, bot
from services.reports import get_sum_by_category, get_weekly_expenses
from utils.charts import plot_pie, plot_bar
from utils.buttons import main_kb

# Состояние для custom сумм
user_sum_state: dict[int, bool] = {}

@dp.message(lambda m: m.text == "📊 Аналитика")
async def show_analytics_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📈 Pie",    callback_data="chart_pie"),
        InlineKeyboardButton(text="📊 Bar",    callback_data="chart_bar"),
        InlineKeyboardButton(text="💲 Сумма", callback_data="sum_menu"),
    ]])
    await message.answer("Выберите отчёт:", reply_markup=kb)

# Pie
@dp.callback_query(lambda c: c.data == "chart_pie")
async def pie_month(query: CallbackQuery):
    user_id = query.from_user.id
    now = datetime.datetime.now(tz=ZoneInfo("Europe/Kyiv"))
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    data = get_sum_by_category(user_id, start, now)
    if not data:
        return await query.answer("Нет трат за этот месяц", show_alert=True)
    # топ-5 + прочие
    items = sorted(data.items(), key=lambda x: x[1], reverse=True)
    top5 = items[:5]
    others = sum(v for _, v in items[5:])
    if others:
        top5.append(("Прочие", others))
    labels, sizes = zip(*top5)
    filename = f"pie_{user_id}.png"
    plot_pie(dict(zip(labels, sizes)), "Pie-аналитика за месяц", filename)
    photo = FSInputFile(path=filename)
    await bot.send_photo(chat_id=user_id, photo=photo)
    await bot.send_message(chat_id=user_id, text="Готово 🥧", reply_markup=main_kb)
    await query.answer()

# Bar
@dp.callback_query(lambda c: c.data == "chart_bar")
async def bar_month(query: CallbackQuery):
    user_id = query.from_user.id
    now = datetime.datetime.now(tz=ZoneInfo("Europe/Kyiv"))
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    data = get_weekly_expenses(user_id, start, now)
    if not data:
        return await query.answer("Нет трат за этот месяц", show_alert=True)
    filename = f"bar_{user_id}.png"
    plot_bar(data, "Bar-аналитика за месяц", filename)
    photo = FSInputFile(path=filename)
    await bot.send_photo(chat_id=user_id, photo=photo)
    await bot.send_message(chat_id=user_id, text="Готово 📊", reply_markup=main_kb)
    await query.answer()

# Sum menu
@dp.callback_query(lambda c: c.data == "sum_menu")
async def sum_menu(query: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="За месяц", callback_data="sum_month"),
        InlineKeyboardButton(text="За год",    callback_data="sum_year"),
        InlineKeyboardButton(text="Свои даты", callback_data="sum_custom"),
    ]])
    await query.message.edit_text("Сумма: выберите период:", reply_markup=kb)
    await query.answer()

@dp.callback_query(lambda c: c.data in ("sum_month", "sum_year"))
async def sum_period(query: CallbackQuery):
    tag = query.data.split("_")[1]
    now = datetime.datetime.now(tz=ZoneInfo("Europe/Kyiv"))
    if tag == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_name = "месяц"
    else:
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        period_name = "год"

    data = get_sum_by_category(query.from_user.id, start, now)
    if not data:
        await query.answer(f"Нет трат за выбранный {period_name}.", show_alert=True)
        return

    # Формируем строки по категориям, каждая с новой строки
    lines = [f"{cat}: {total:.2f} ₴" for cat, total in data.items()]
    total_sum = sum(data.values())
    lines.append(f"Всего: {total_sum:.2f} ₴")

    text = f"Сумма трат по категориям за {period_name}:\n" + "\n".join(lines)
    # удаляем inline-кнопки старого меню
    await query.message.edit_reply_markup(reply_markup=None)
    # отправляем новый ответ с main_kb
    await query.message.answer(text, reply_markup=main_kb)
    await query.answer()

# Обработка «Свои даты»
@dp.callback_query(lambda c: c.data == "sum_custom")
async def sum_custom(query: CallbackQuery):
    user_sum_state[query.from_user.id] = True
    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.answer(
        "Введите диапазон YYYY-MM-DD–YYYY-MM-DD:",
        reply_markup=ReplyKeyboardRemove()
    )
    await query.answer()

@dp.message(lambda m: user_sum_state.get(m.from_user.id))
async def sum_custom_input(message: Message):
    text = message.text.strip()
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})[–-](\d{4}-\d{2}-\d{2})", text)
    if not m:
        return await message.answer(
            "Неверный формат. Пример: 2025-06-01–2025-06-30",
            reply_markup=main_kb
        )

    start = datetime.datetime.fromisoformat(m.group(1)).replace(tzinfo=ZoneInfo("Europe/Kyiv"))
    end   = datetime.datetime.fromisoformat(m.group(2)).replace(tzinfo=ZoneInfo("Europe/Kyiv"))
    data = get_sum_by_category(message.from_user.id, start, end)

    if not data:
        await message.answer("Нет трат за выбранный период.", reply_markup=main_kb)
    else:
        lines = [f"{cat}: {total:.2f} ₴" for cat, total in data.items()]
        total_sum = sum(data.values())
        lines.append(f"Всего: {total_sum:.2f} ₴")
        text_resp = f"Сумма трат по категориям за {start.date()}–{end.date()}:\n" + "\n".join(lines)
        await message.answer(text_resp, reply_markup=main_kb)

    user_sum_state.pop(message.from_user.id, None)