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

# состояние пользователя для custom pie
user_analytics_state: dict[int, dict] = {}

@dp.message(lambda m: m.text == "📊 Аналитика")
async def show_analytics_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📈 Pie-круг", callback_data="chart_pie"),
        InlineKeyboardButton(text="📊 Bar-столбцы", callback_data="chart_bar"),
    ]])
    await message.answer("Выберите тип графика:", reply_markup=kb)

@dp.callback_query(lambda c: c.data == "chart_pie")
async def choose_pie(query: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Месяц",    callback_data="pie_month")],
        [InlineKeyboardButton(text="Квартал", callback_data="pie_quarter")],
        [InlineKeyboardButton(text="Год",      callback_data="pie_year")],
        [InlineKeyboardButton(text="Свои даты", callback_data="pie_custom")],
    ])
    await query.message.edit_text("Pie: выберите период:", reply_markup=kb)
    await query.answer()

@dp.callback_query(lambda c: c.data == "chart_bar")
async def choose_bar(query: CallbackQuery):
    await generate_bar(query)

@dp.callback_query(lambda c: c.data in ("pie_month", "pie_quarter", "pie_year"))
async def pie_period(query: CallbackQuery):
    now = datetime.datetime.now(tz=ZoneInfo("Europe/Kyiv"))
    tag = query.data.split("_")[1]
    if tag == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif tag == "quarter":
        quarter_start = ((now.month - 1)//3)*3 + 1
        start = now.replace(month=quarter_start, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    await generate_pie(query, start, now)

@dp.callback_query(lambda c: c.data == "pie_custom")
async def pie_custom(query: CallbackQuery):
    user_analytics_state[query.from_user.id] = {"mode": "pie_custom"}
    # удаляем inline-кнопки
    await query.message.edit_reply_markup(reply_markup=None)
    # просим ввести диапазон через обычное сообщение
    await query.message.answer(
        "Введите диапазон YYYY-MM-DD–YYYY-MM-DD:",
        reply_markup=ReplyKeyboardRemove()
    )
    await query.answer()

@dp.message(lambda m: user_analytics_state.get(m.from_user.id, {}).get("mode") == "pie_custom")
async def pie_custom_input(message: Message):
    text = message.text.strip()
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})[–-](\d{4}-\d{2}-\d{2})", text)
    if not m:
        return await message.answer("Неверный формат. Пример: 2025-06-01–2025-06-30")
    start = datetime.datetime.fromisoformat(m.group(1)).replace(tzinfo=ZoneInfo("Europe/Kyiv"))
    end   = datetime.datetime.fromisoformat(m.group(2)).replace(tzinfo=ZoneInfo("Europe/Kyiv"))
    await generate_pie(message, start, end)
    user_analytics_state.pop(message.from_user.id, None)

async def generate_pie(source, start: datetime.datetime, end: datetime.datetime):
    user_id = source.from_user.id
    data = get_sum_by_category(user_id, start, end)
    if not data:
        return await source.answer("Нет трат за выбранный период", show_alert=True)
    items = sorted(data.items(), key=lambda x: x[1], reverse=True)
    top5 = items[:5]
    others = sum(v for _, v in items[5:])
    if others:
        top5.append(("Прочие", others))
    labels, sizes = zip(*top5)
    filename = f"pie_{user_id}.png"
    plot_pie(dict(zip(labels, sizes)), f"Pie {start.date()}–{end.date()}", filename)
    photo = FSInputFile(path=filename)
    await bot.send_photo(chat_id=user_id, photo=photo)
    await bot.send_message(chat_id=user_id, text="Готово. 🥧", reply_markup=main_kb)

async def generate_bar(source):
    user_id = source.from_user.id
    now = datetime.datetime.now(tz=ZoneInfo("Europe/Kyiv"))
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    data = get_weekly_expenses(user_id, start, now)
    if not data:
        return await source.answer("Нет трат за этот месяц", show_alert=True)
    filename = f"bar_{user_id}.png"
    plot_bar(data, f"Bar {start.date()}–{now.date()}", filename)
    photo = FSInputFile(path=filename)
    await bot.send_photo(chat_id=user_id, photo=photo)
    await bot.send_message(chat_id=user_id, text="Готово. 📊", reply_markup=main_kb)