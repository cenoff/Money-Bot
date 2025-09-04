from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sql import (
    add_expense,
    add_saving,
    get_month_savings,
    get_month_expenses_by_category,
    get_month_total_expenses,
    get_year_expenses,
)
from keyboard import category_stats_keyboard, saving_options

router = Router()


class SpendInput(StatesGroup):
    waiting_for_category = State()
    waiting_for_amount = State()


class SaveInput(StatesGroup):
    waiting_for_amount = State()


category_temp = {}


@router.message(F.text == "💸 Потратил всего")
async def choose_category_for_stats(message: Message):
    total = get_month_total_expenses(message.from_user.id)
    await message.answer(
        f"📊 Ты потратил в этом месяце всего: <b>{total:.2f}€</b>\n"
        f"Выбери категорию, чтобы посмотреть детальнее:",
        reply_markup=category_stats_keyboard(),
    )


@router.message(F.text == "💰 Сэкономил")
async def saving_info(message: Message, state: FSMContext):
    total = get_month_savings(message.from_user.id)
    await message.answer(
        f"💰 Ты сэкономил в этом месяце: {total:.2f}€", reply_markup=saving_options()
    )


@router.callback_query(F.data == "add_saving")
async def ask_saving_input(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("💬 Введи, сколько ты сегодня сэкономил:")
    await state.set_state(SaveInput.waiting_for_amount)


@router.message(SaveInput.waiting_for_amount)
async def save_saving_input(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        add_saving(message.from_user.id, amount)
        total = get_month_savings(message.from_user.id)
        await message.answer(
            f"✅ Добавлено! 💰 Всего сэкономлено в этом месяце: {total:.2f}€"
        )
    except:
        await message.answer("❗ Введи число, например: 5.50")
    await state.clear()


@router.message(
    F.text.in_(
        [
            "🍔 Хрючево",
            "🚬 Пошмокать",
            "🎉 Гульки",
            "👕 Тряпье",
            "🖥 Техника",
            "💅 Бьюти",
            "👱🏿‍♀️ Шалавы",
        ]
    )
)
async def ask_spend_amount(message: Message, state: FSMContext):
    category_emoji = message.text
    emoji_to_category = {
        "🍔 Хрючево": "food",
        "🚬 Пошмокать": "smoking",
        "🎉 Гульки": "entertainment",
        "👕 Тряпье": "cloth",
        "🖥 Техника": "tech",
        "💅 Бьюти": "beauty",
        "👱🏿‍♀️ Шалавы": "sluts",
    }
    category = emoji_to_category[category_emoji]
    category_temp[message.from_user.id] = category
    await state.set_state(SpendInput.waiting_for_amount)
    await message.answer(f"💬 Введи сумму, которую потратил на {category_emoji}:")


@router.message(SpendInput.waiting_for_amount)
async def spend_input_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        category = category_temp.get(message.from_user.id)
        add_expense(message.from_user.id, category, amount)
        await message.answer(f"✅ Добавлено: {amount:.2f}€ на {category}")
    except:
        await message.answer("❗ Введи число, например: 12.00")
    await state.clear()


@router.callback_query(F.data == "stat_year")
async def year_stats(callback: CallbackQuery):
    rows = get_year_expenses(callback.from_user.id)
    if not rows:
        await callback.message.answer("📭 У тебя пока нет трат за этот год.")
        return

    total = 0
    category_names = {
        "food": "🍔 Хрючево",
        "smoking": "🚬 Пошмокать",
        "entertainment": "🎉 Гульки",
        "cloth": "👕 Тряпье",
        "tech": "🖥 Техника",
        "beauty": "💅 Бьюти",
        "sluts": "👱🏿‍♀️ Шалавы",
    }

    text = "<b>📆 Твоя статистика за этот год:</b>\n\n"
    for cat, sum_ in rows:
        emoji_name = category_names.get(cat, f"• {cat.capitalize()}")
        text += f"{emoji_name:<15} — {sum_:.2f}€\n"
        total += sum_

    text += f"\n<b>💸 Всего потрачено за год: {total:.2f}€</b>"
    await callback.message.answer(text)


@router.callback_query(F.data.startswith("stat_"))
async def category_stat_result(callback: CallbackQuery):
    category_map = {
        "stat_food": ("food", "🍔 Хрючево"),
        "stat_smoking": ("smoking", "🚬 Пошмокать"),
        "stat_entertainment": ("entertainment", "🎉 Гульки"),
        "stat_cloth": ("cloth", "👕 Тряпье"),
        "stat_tech": ("tech", "🖥 Техника"),
        "stat_beauty": ("beauty", "💅 Бьюти"),
        "stat_sluts": ("sluts", "👱🏿‍♀️ Шалавы"),
    }

    category_data = category_map.get(callback.data)
    if not category_data:
        await callback.message.answer("❌ Неизвестная категория.")
        return

    category_key, category_label = category_data
    total = get_month_expenses_by_category(callback.from_user.id, category_key)

    await callback.message.answer(
        f"📊 В этом месяце ты потратил на {category_label}: <b>{total:.2f}€</b>"
    )
