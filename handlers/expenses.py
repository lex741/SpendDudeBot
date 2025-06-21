# handlers/expenses.py

import datetime
from zoneinfo import ZoneInfo

from aiogram.types import (
    Message, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardRemove, CallbackQuery
)
from bot_config import dp
from services.expenses import (
    add_expense, get_recent_expenses, get_user_balance
)
from services.categories import get_categories, get_category_by_id, has_expenses, delete_category_and_expenses
from utils.buttons import main_kb

# состояние при добавлении траты
user_tx: dict[int, dict] = {}

# --- 1) Начало добавления ---
@dp.message(lambda m: m.text == "➕ Добавить трату")
async def start_add(message: Message):
    user_tx[message.from_user.id] = {}
    await message.answer("Введите сумму траты (число):", reply_markup=ReplyKeyboardRemove())

# --- 2) Сумма ---
@dp.message(lambda m: m.from_user.id in user_tx and 'amount' not in user_tx[m.from_user.id])
async def enter_amount(message: Message):
    try:
        amt = float(message.text.replace(',', '.'))
    except ValueError:
        return await message.answer("Неверный формат. Введите число, например «250.50»:")
    user_tx[message.from_user.id]['amount'] = amt
    await message.answer("Добавьте комментарий или отправьте «-» для без комментария:")

# --- 3) Комментарий ---
@dp.message(lambda m: m.from_user.id in user_tx
                         and 'amount' in user_tx[m.from_user.id]
                         and 'comment' not in user_tx[m.from_user.id])
async def enter_comment(message: Message):
    comment = "" if message.text == '-' else message.text.strip()
    tx = user_tx[message.from_user.id]
    tx['comment'] = comment

    cats = get_categories(message.from_user.id)
    if not cats:
        await message.answer("Сначала создайте хотя бы одну категорию.", reply_markup=main_kb)
        user_tx.pop(message.from_user.id, None)
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=c.name, callback_data=f"tx_cat_{c.id}")]
            for c in cats
        ]
    )
    await message.answer("Выберите категорию:", reply_markup=kb)

# --- 4) Выбор категории и сохранение траты ---
@dp.callback_query(lambda c: c.data and c.data.startswith("tx_cat_"))
async def choose_category(query: CallbackQuery):
    user_id = query.from_user.id
    cat_id = int(query.data.split("_", 2)[2])
    data = user_tx.get(user_id)
    if not data:
        return await query.answer("Сессия протухла — начните заново.", show_alert=True)

    # Преобразуем время UTC → Europe/Kyiv
    utc_dt = query.message.date.replace(tzinfo=datetime.timezone.utc)
    local_dt = utc_dt.astimezone(ZoneInfo("Europe/Kyiv"))

    exp = add_expense(
        user_id=user_id,
        amount=data['amount'],
        comment=data['comment'],
        category_id=cat_id,
        date=local_dt  # теперь сохраняем уже локальное время
    )
    balance = get_user_balance(user_id)
    category = get_category_by_id(cat_id)
    cat_name = category.name if category else "—"

    await query.answer("Трата добавлена")
    await query.message.answer(
        f"✅ Вы потратили {exp.amount:.2f} в категории «{cat_name}»\n"
        f"Комментарий: {exp.comment or '—'}\n"
        f"Время: {exp.date.strftime('%Y-%m-%d %H:%M')}\n"
        f"Остаток: {balance:.2f}",
        reply_markup=main_kb
    )
    user_tx.pop(user_id, None)

# --- 5) История последних 5 трат с названием категории ---
@dp.message(lambda m: m.text == "📜 История")
async def show_history(message: Message):
    lst = get_recent_expenses(message.from_user.id, limit=5)
    if not lst:
        return await message.answer("У вас ещё нет трат.", reply_markup=main_kb)

    lines = []
    for e in lst:
        cat = get_category_by_id(e.category_id)
        cat_name = cat.name if cat else "—"
        ts = e.date.strftime("%Y-%m-%d %H:%M")
        lines.append(f"{ts} — {e.amount:.2f}  [{cat_name}]  «{e.comment or '-'}»")

    await message.answer("Последние траты:\n" + "\n".join(lines), reply_markup=main_kb)
