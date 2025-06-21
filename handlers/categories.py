import re
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from bot_config import dp
from services.categories import (
    get_categories,
    add_category,
    delete_category,
    has_expenses,
    delete_category_and_expenses,
)
from utils.buttons import main_kb

# временное хранилище состояния пользователя при добавлении новой категории
user_states: dict[int, str] = {}

async def send_categories(user_id: int, target):
    """
    Высылает список категорий пользователю и кнопки Добавить/Удалить.
    target: объект с методом answer (Message или CallbackQuery.message)
    """
    cats = get_categories(user_id)
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
    await target.answer(text, reply_markup=kb)

@dp.message(lambda m: m.text == "📂 Категории")
async def show_categories_message(message: Message):
    await send_categories(message.from_user.id, message)

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
    await query.message.answer(
        "Выберите категорию для удаления:",
        reply_markup=kb
    )
    await query.answer()

# Обработка простого удаления по позиции del_<номер>
@dp.callback_query(lambda c: c.data and re.fullmatch(r"del_\d+", c.data))
async def on_delete_choice(query: CallbackQuery):
    pos = int(query.data.split("_", 1)[1])
    user_id = query.from_user.id
    cats = get_categories(user_id)
    if pos < 1 or pos > len(cats):
        return await query.answer("Неверный выбор", show_alert=True)

    cat = cats[pos - 1]
    if has_expenses(user_id, cat.id):
        # подтверждение удаления и трат
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="✅ Удалить всё", callback_data=f"del_confirm_{pos}"),
                InlineKeyboardButton(text="❌ Отмена",    callback_data="cat_delete_cancel"),
            ]]
        )
        await query.message.edit_text(
            f"В категории «{cat.name}» есть траты.\nУдалить категорию и все её траты?",
            reply_markup=kb
        )
        await query.answer()
    else:
        # простое удаление
        delete_category(user_id, cat.id)
        await query.answer("Категория удалена")
        await send_categories(user_id, query.message)

# Подтверждение удаления вместе с тратами del_confirm_<номер>
@dp.callback_query(lambda c: c.data and re.fullmatch(r"del_confirm_\d+", c.data))
async def on_delete_confirm(query: CallbackQuery):
    pos = int(query.data.rsplit("_", 1)[1])
    user_id = query.from_user.id
    cats = get_categories(user_id)
    if pos < 1 or pos > len(cats):
        return await query.answer("Неверный выбор", show_alert=True)

    real_id = cats[pos - 1].id
    delete_category_and_expenses(user_id, real_id)
    await query.answer("Категория и все её траты удалены")
    await send_categories(user_id, query.message)

@dp.callback_query(lambda c: c.data == "cat_delete_cancel")
async def on_delete_cancel(query: CallbackQuery):
    await query.answer("Удаление отменено", show_alert=True)
    await send_categories(query.from_user.id, query.message)

@dp.message(lambda m: user_states.get(m.from_user.id) == "adding")
async def on_new_category(message: Message):
    name = message.text.strip()
    user_id = message.from_user.id
    existing = [c.name for c in get_categories(user_id)]
    if name in existing:
        await message.answer(f"Категория «{name}» уже существует.", reply_markup=main_kb)
    else:
        add_category(user_id, name)
        await message.answer(f"Категория «{name}» добавлена.", reply_markup=main_kb)
    user_states.pop(user_id, None)