# handlers/categories.py
from aiogram import types
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardRemove
from bot_config import dp
from services.categories import get_categories, add_category, delete_category
from utils.buttons import main_kb

# Храним состояние «ожидание ввода названия» для каждого пользователя
user_states: dict[int, str] = {}

@dp.message(lambda m: m.text == "📂 Категории")
async def show_categories(message: Message):
    cats = get_categories(message.from_user.id)
    if cats:
        lines = [f"{i}. {cat.name}" for i, cat in enumerate(cats, start=1)]
        text = "Ваши категории:\n" + "\n".join(lines)
    else:
        text = "У вас ещё нет ни одной категории."
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="➕ Добавить", callback_data="cat_add"),
            InlineKeyboardButton(text="➖ Удалить", callback_data="cat_delete"),
        ]]
    )
    await message.answer(text, reply_markup=kb)

@dp.callback_query(lambda c: c.data == "cat_add")
async def on_add_button(query: CallbackQuery):
    user_states[query.from_user.id] = "adding"
    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.answer(
        "Напишите название новой категории:",
        reply_markup=ReplyKeyboardRemove()
    )
    await query.answer()

@dp.callback_query(lambda c: c.data == "cat_delete")
async def on_delete_button(query: CallbackQuery):
    cats = get_categories(query.from_user.id)
    if not cats:
        await query.answer("Нет категорий для удаления", show_alert=True)
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{i}. {cat.name}", callback_data=f"del_{i}")]
            for i, cat in enumerate(cats, start=1)
        ]
    )
    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.answer("Выберите категорию для удаления:", reply_markup=kb)
    await query.answer()

@dp.callback_query(lambda c: c.data and c.data.startswith("del_"))
async def on_delete_choice(query: CallbackQuery):
    pos = int(query.data.split("_", 1)[1])
    cats = get_categories(query.from_user.id)
    if 1 <= pos <= len(cats):
        cat = cats[pos-1]
        delete_category(query.from_user.id, cat.id)
        await query.answer(f"Категория «{cat.name}» удалена")
    else:
        await query.answer("Неверный выбор", show_alert=True)

    # После удаления — перерисуем список заново
    cats = get_categories(query.from_user.id)
    if cats:
        lines = [f"{i}. {c.name}" for i, c in enumerate(cats, start=1)]
        text = "Ваши категории:\n" + "\n".join(lines)
    else:
        text = "У вас ещё нет ни одной категории."
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="➕ Добавить", callback_data="cat_add"),
            InlineKeyboardButton(text="➖ Удалить", callback_data="cat_delete"),
        ]]
    )
    await query.message.edit_text(text, reply_markup=kb)

@dp.message(lambda m: user_states.get(m.from_user.id) == "adding")
async def on_new_category(message: Message):
    name = message.text.strip()
    existing = [c.name for c in get_categories(message.from_user.id)]
    if name in existing:
        await message.answer(f"Категория «{name}» уже существует.", reply_markup=main_kb)
    else:
        cat = add_category(message.from_user.id, name)
        await message.answer(f"Категория «{cat.name}» добавлена.", reply_markup=main_kb)
    user_states.pop(message.from_user.id, None)
