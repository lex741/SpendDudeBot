import re
import datetime
from zoneinfo import ZoneInfo
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardRemove,
)
from bot_config import dp
from services.expenses import (
    get_recent_expenses,
    get_expenses_filtered,
    delete_expense,
)
from services.categories import get_categories, get_category_by_id
from utils.buttons import main_kb

# Состояние фильтрации и промежуточные шаги
history_state: dict[int, dict] = {}

@dp.message(lambda m: m.text == "📜 История")
async def show_history_menu(message: Message):
    user_id = message.from_user.id
    history_state[user_id] = {}
    await send_history_list(user_id, message)

async def send_history_list(user_id: int, target):
    state = history_state.get(user_id, {})
    # Определяем set расходов
    if state.get("mode") == "category":
        cat_id = state["category_id"]
        expenses = get_expenses_filtered(user_id, category_id=cat_id)
        header = f"История по категории «{get_category_by_id(cat_id).name}»:\n"
    elif state.get("mode") in ("period_month", "period_year"):
        start, end = state["start"], state["end"]
        expenses = get_expenses_filtered(user_id, start=start, end=end)
        header = f"История за период {start.date()}–{end.date()}:\n"
    elif state.get("mode") == "period_custom":
        start, end = state["start"], state["end"]
        expenses = get_expenses_filtered(user_id, start=start, end=end)
        header = f"История за {start.date()}–{end.date()}:\n"
    elif state.get("mode") == "cat_period":
        cat_id = state["category_id"]
        start, end = state["start"], state["end"]
        expenses = get_expenses_filtered(user_id, category_id=cat_id, start=start, end=end)
        header = f"История «{get_category_by_id(cat_id).name}» за {start.date()}–{end.date()}:\n"
    else:
        expenses = get_recent_expenses(user_id, limit=10)
        header = "История последних 10 трат:\n"

    if not expenses:
        return await target.answer("Транзакции не найдены.", reply_markup=main_kb)

    lines = []
    for idx, e in enumerate(expenses, start=1):
        ts = e.date.astimezone(ZoneInfo("Europe/Kyiv")).strftime("%Y-%m-%d %H:%M")
        cat = get_category_by_id(e.category_id)
        cat_name = cat.name if cat else '-'
        lines.append(f"{idx}. {ts} — {e.amount:.2f} ₴ — {cat_name} — {e.comment or '-'}")

    # Основное меню: фильтры и удаление
    rows = [[
        InlineKeyboardButton(text="По категории", callback_data="hist_filter_cat"),
        InlineKeyboardButton(text="По периоду", callback_data="hist_filter_period_menu"),
        InlineKeyboardButton(text="Кат+Период", callback_data="hist_filter_cat_period"),
    ], [
        InlineKeyboardButton(text="Удалить транзакцию", callback_data="hist_start_delete")
    ]]
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await target.answer(header + "\n".join(lines), reply_markup=kb)

# Удаление по два шага
@dp.callback_query(lambda c: c.data == "hist_start_delete")
async def start_delete_flow(query: CallbackQuery):
    user_id = query.from_user.id
    state = history_state.get(user_id, {})
    # получаем текущий список
    if state.get("mode") == "category":
        exps = get_expenses_filtered(user_id, category_id=state["category_id"])
    elif state.get("mode") in ("period_month","period_year","period_custom"):
        exps = get_expenses_filtered(user_id, start=state.get("start"), end=state.get("end"))
    elif state.get("mode") == "cat_period":
        exps = get_expenses_filtered(user_id, category_id=state["category_id"], start=state.get("start"), end=state.get("end"))
    else:
        exps = get_recent_expenses(user_id, limit=10)

    if not exps:
        return await query.answer("Нет трат для удаления.", show_alert=True)
    await query.message.edit_reply_markup(reply_markup=None)
    # меню выбора номера
    rows = [[InlineKeyboardButton(text=str(idx), callback_data=f"hist_delete_{idx}")]
            for idx, _ in enumerate(exps, start=1)]
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await query.message.answer("Выберите номер транзакции:", reply_markup=kb)
    await query.answer()

@dp.callback_query(lambda c: c.data.startswith("hist_delete_"))
async def delete_by_position(query: CallbackQuery):
    user_id = query.from_user.id
    pos = int(query.data.split("_", 2)[2])
    state = history_state.get(user_id, {})
    if state.get("mode") == "category":
        exps = get_expenses_filtered(user_id, category_id=state["category_id"])
    elif state.get("mode") in ("period_month","period_year","period_custom"):
        exps = get_expenses_filtered(user_id, start=state.get("start"), end=state.get("end"))
    elif state.get("mode") == "cat_period":
        exps = get_expenses_filtered(user_id, category_id=state["category_id"], start=state.get("start"), end=state.get("end"))
    else:
        exps = get_recent_expenses(user_id, limit=10)

    if pos < 1 or pos > len(exps):
        return await query.answer("Неверный номер", show_alert=True)
    exp = exps[pos-1]
    ok = delete_expense(user_id, exp.id)
    await query.answer("Трата удалена ✅" if ok else "Ошибка ❌")
    await send_history_list(user_id, query.message)

# Фильтр по категории
@dp.callback_query(lambda c: c.data == "hist_filter_cat")
async def filter_by_category(query: CallbackQuery):
    user_id = query.from_user.id
    cats = get_categories(user_id)
    if not cats:
        return await query.answer("У вас нет категорий", show_alert=True)
    rows = [[InlineKeyboardButton(text=c.name, callback_data=f"hist_cat_{c.id}")] for c in cats]
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    history_state[user_id] = {"mode": "category"}
    await query.message.edit_text("Выберите категорию:", reply_markup=kb)
    await query.answer()

@dp.callback_query(lambda c: c.data.startswith("hist_cat_"))
async def handle_category_choice(query: CallbackQuery):
    user_id = query.from_user.id
    cat_id = int(query.data.split("_", 2)[2])
    history_state[user_id]["category_id"] = cat_id
    await query.answer()
    await send_history_list(user_id, query.message)

# Новое меню по периоду: месяц, год, свои даты
@dp.callback_query(lambda c: c.data == "hist_filter_period_menu")
async def filter_period_menu(query: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="За месяц", callback_data="hist_period_month"),
        InlineKeyboardButton(text="За год",    callback_data="hist_period_year"),
        InlineKeyboardButton(text="Свои даты", callback_data="hist_period_custom"),
    ]])
    history_state[query.from_user.id] = {}
    await query.message.edit_text("Выберите период:", reply_markup=kb)
    await query.answer()

@dp.callback_query(lambda c: c.data in ("hist_period_month","hist_period_year"))
async def handle_period_choice(query: CallbackQuery):
    tag = query.data.split("_")[2]
    now = datetime.datetime.now(tz=ZoneInfo("Europe/Kyiv"))
    if tag == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        state_mode = "period_month"
    else:
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        state_mode = "period_year"
    history_state[query.from_user.id] = {"mode": state_mode, "start": start, "end": now}
    await query.answer()
    await send_history_list(query.from_user.id, query.message)

@dp.callback_query(lambda c: c.data == "hist_period_custom")
async def handle_period_custom(query: CallbackQuery):
    user_id = query.from_user.id
    history_state[user_id] = {"mode": "period_custom"}
    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.answer(
        "Введите диапазон YYYY-MM-DD–YYYY-MM-DD:",
        reply_markup=ReplyKeyboardRemove()
    )
    await query.answer()

@dp.message(lambda m: history_state.get(m.from_user.id, {}).get("mode") == "period_custom")
async def handle_custom_period_input(message: Message):
    user_id = message.from_user.id
    text_input = message.text.strip()
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})[–-](\d{4}-\d{2}-\d{2})", text_input)
    if not match:
        return await message.answer("Неверный формат. Пример: 2025-06-01–2025-06-30")
    start = datetime.datetime.fromisoformat(match.group(1)).replace(tzinfo=ZoneInfo("Europe/Kyiv"))
    end   = datetime.datetime.fromisoformat(match.group(2)).replace(tzinfo=ZoneInfo("Europe/Kyiv"))
    # Получаем траты за указанный период
    expenses = get_expenses_filtered(user_id, start=start, end=end)
    if not expenses:
        await message.answer("Транзакции не найдены.", reply_markup=main_kb)
    else:
        header = f"История за {start.date()}–{end.date()}:\n"
        lines = []
        for idx, e in enumerate(expenses, start=1):
            ts = e.date.astimezone(ZoneInfo("Europe/Kyiv")).strftime("%Y-%m-%d %H:%M")
            cat = get_category_by_id(e.category_id)
            cat_name = cat.name if cat else '-'
            lines.append(f"{idx}. {ts} — {e.amount:.2f} ₴ — {cat_name} — {e.comment or '-'}")
        # Отправляем результат и показываем главное меню
        await message.answer(header + "\n".join(lines), reply_markup=main_kb)
    # Сбрасываем состояние фильтрации
    history_state.pop(user_id, None)