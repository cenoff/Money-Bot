import logging
import os

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message

from constants import EMOJI_TO_CATEGORY
from graphs import call_graph_creator
from keyboard import (
    category_subscriptions_keyboard,
    reports_keyboard,
    saving_options,
    subscriptions_keyboard,
)
from sql import (
    add_expense,
    add_new_subscription,
    add_saving,
    create_report,
    disable_month_subscription,
    enable_month_subscription,
    get_all_categories_and_values,
    get_month_subscriptions_expenses,
    get_month_total_expenses,
    get_savings,
    get_subscriptions_breakdown,
    get_year_expenses,
)

logger = logging.getLogger(__name__)

router = Router()


class SpendInput(StatesGroup):
    waiting_for_category = State()
    waiting_for_amount = State()
    waiting_for_subscription_name = State()
    waiting_for_subscription_amount = State()


class SaveInput(StatesGroup):
    waiting_for_amount = State()


class Choose(StatesGroup):
    waiting_for_subscription_to_delete = State()
    disable_subscriptions_list = State()
    disable_subscription = State()
    send_document = State()


def remove_temp_files(path: str):
    if os.path.exists(path):
        os.remove(path)


def parse_amount(text: str) -> float | None:
    try:
        amount = float(text.replace(",", "."))

        if amount <= 0:
            return None

        return amount

    except ValueError:
        return None


@router.callback_query(F.data.startswith("back_to:"))
async def go_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    back_to = callback.data.split("back_to:")[1]
    if back_to == "subscriptions":
        await callback.message.delete()
        await subscriptions(callback, callback.from_user.id)


@router.message(F.text == "📊 Statistics")
async def choose_category_for_stats(message: Message):
    user_id = message.from_user.id

    total_expenses = await get_month_total_expenses(user_id)
    total_savings = await get_savings(user_id, is_month_saving=True)
    total_year_expenses = await get_year_expenses(user_id)
    total_year_savings = await get_savings(user_id, is_month_saving=False)

    data = await get_all_categories_and_values(user_id)
    month_subscriptions = await get_month_subscriptions_expenses(user_id)

    if month_subscriptions > 0:
        data.append(("subscriptions", month_subscriptions))

    graph = await call_graph_creator(data)
    photo = FSInputFile(graph)

    caption = (
        "📊 <b>Your Statistics:</b>\n\n"
        f"💸 <b>This Month:</b>\n"
        f"Spent: <code>{total_expenses:.2f}€</code>\n"
        f"Saved: <code>{total_savings:.2f}€</code>\n\n"
        f"📅 <b>This Year:</b>\n"
        f"Spent: <code>{total_year_expenses:.2f}€</code>\n"
        f"Saved: <code>{total_year_savings:.2f}€</code>\n\n"
        f"📄 Download reports below 👇"
    )

    await message.answer_photo(
        photo=photo,
        caption=caption,
        reply_markup=reports_keyboard,
        parse_mode="HTML",
    )

    remove_temp_files(graph)


@router.callback_query(F.data.startswith("sub_enable:"))
async def enable_subscription(callback: CallbackQuery, state: FSMContext):
    name = callback.data.split("sub_enable:")[1]
    await enable_month_subscription(callback.from_user.id, name)
    await state.clear()
    await callback.answer(f"✅ Subscription {name} activated!")
    await callback.message.delete()


@router.callback_query(F.data == "add_subscription")
async def add_subscription(callback: CallbackQuery, state: FSMContext):
    is_active = False
    time_filter = False

    rows = await get_subscriptions_breakdown(
        callback.from_user.id, is_active, time_filter
    )
    names: list[str] = [name for name, _ in rows]
    keyboard = await subscriptions_keyboard(names, is_active)
    message = (
        "💬 <b>Enter subscription name</b>\n\nOr select an inactive one below 👇"
        if rows
        else "💬 <b>Enter subscription name</b>"
    )

    await callback.message.edit_text(
        message,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    await state.set_state(SpendInput.waiting_for_subscription_name)


@router.message(SpendInput.waiting_for_subscription_name)
async def subscription_name(message: Message, state: FSMContext):
    try:
        await state.update_data(subscription_name=message.text)
        await state.set_state(SpendInput.waiting_for_subscription_amount)
        await message.answer("Enter the monthly subscription price:")

    except ValueError:
        await message.answer("❗ Please provide a valid subscription name!")


@router.message(SpendInput.waiting_for_subscription_amount)
async def subscription_price(message: Message, state: FSMContext):
    amount = parse_amount(message.text)
    if amount is None:
        await message.answer("❗ Please enter a number, e.g.: 5.50")
        return

    data = await state.get_data()
    subscription_name = data.get("subscription_name")
    await add_new_subscription(message.from_user.id, subscription_name, amount)
    await message.answer(
        f"✅ <b>Added</b>\n\n{subscription_name}\n<code>{amount:.2f}€</code> per month",
        parse_mode="HTML",
    )

    await state.clear()


@router.callback_query(F.data == "disable_subscriptions_list")
async def disable_subscription_list(callback: CallbackQuery, state: FSMContext):
    is_active = True
    time_filter = True

    rows = await get_subscriptions_breakdown(
        callback.from_user.id, is_active, time_filter
    )
    names: list[str] = [name for name, _ in rows]
    keyboard = await subscriptions_keyboard(names, is_active)

    await callback.message.edit_text(
        "📝 <b>Select a subscription to disable:</b>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    await state.set_state(Choose.disable_subscription)


@router.callback_query(F.data.startswith("sub_select:"))
async def disable_subscription(callback: CallbackQuery, state: FSMContext):
    name = callback.data.split("sub_select:")[1]

    await disable_month_subscription(callback.from_user.id, name)
    await callback.answer(f"🗑 Subscription {name} disabled!")
    await callback.message.delete()


@router.message(F.text == "📝 Subscriptions")
async def appear_subscriptions_menu(message: Message):
    await subscriptions(message, message.from_user.id)


async def subscriptions(target, user_id: int):
    is_active = True
    time_filter = True

    rows = await get_subscriptions_breakdown(user_id, is_active, time_filter)
    total = await get_month_subscriptions_expenses(user_id)
    lines = [f"-  {name}: {amount:.2f}€" for name, amount in rows]

    message_obj = target.message if hasattr(target, "message") else target

    if not rows:
        await message_obj.answer(
            "📝 <b>Your subscriptions:</b>\n\n"
            "You have no active subscriptions yet.\n"
            "Add your first one by pressing the button below! 👇",
            reply_markup=category_subscriptions_keyboard,
            parse_mode="HTML",
        )
        return

    lines = []
    for name, amount in rows:
        lines.append(f"  - <b>{name}</b>: <code>{amount:.2f}€</code>")

    total_message = (
        "📝 <b>Your subscriptions:</b>\n\n" + "\n".join(lines) + "\n\n"
        f"💰 Monthly: <code>{total:.2f}€</code>\n"
        f"📅 Yearly: <code>{total * 12:.2f}€</code>"
    )

    await message_obj.answer(
        total_message,
        reply_markup=category_subscriptions_keyboard,
        parse_mode="HTML",
    )


@router.message(F.text == "📉 Saved")
async def savings(message: Message):
    user_id = message.from_user.id
    month_savings = await get_savings(user_id, is_month_saving=True)
    year_savings = await get_savings(user_id, is_month_saving=False)

    keyboard = saving_options
    savings_message = (
        "📉 <b>Your Savings:</b>\n\n"
        f"💰 This month: <code>{month_savings:.2f}€</code>\n"
        f"📅 Saved this year: <code>{year_savings:.2f}€</code>\n\n"
    )

    await message.answer(savings_message, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "add_saving")
async def ask_saving_input(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("💬 Enter how much you saved today:")
    await state.set_state(SaveInput.waiting_for_amount)


@router.message(SaveInput.waiting_for_amount)
async def save_saving_input(message: Message, state: FSMContext):
    amount = parse_amount(message.text)
    if amount is None:
        await message.answer("❗ Please enter a number, e.g.: 5.50")
        return
    await add_saving(message.from_user.id, amount)
    total = await get_savings(message.from_user.id, is_month_saving=True)
    await message.answer(
        f"✅ <b>Added</b>\n\nTotal saved this month: <code>{total:.2f}€</code>",
        parse_mode="HTML",
    )

    await state.clear()


@router.message(F.text.in_(list(EMOJI_TO_CATEGORY.keys())))
async def ask_spend_amount(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(SpendInput.waiting_for_amount)
    await message.answer(f"💬 Enter the amount you spent on {message.text}:")


@router.message(SpendInput.waiting_for_amount)
async def spend_input_amount(message: Message, state: FSMContext):
    amount = parse_amount(message.text)
    if amount is None:
        await message.answer("❗ Please enter a number, e.g.: 5.50")
        return
    data = await state.get_data()
    category = data.get("category")

    await add_expense(message.from_user.id, category, amount)
    await message.answer(
        f"✅ <b>Added!</b>\n\n💰 <code>{amount:.2f}€</code> for <b>{category}</b>",
        parse_mode="HTML",
    )

    await state.clear()


@router.callback_query(F.data.startswith("report:"))
async def reports(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    report_type = callback.data.split("report:")[1]
    is_all_time_report = True

    if "month" in report_type:
        is_all_time_report = False

    try:
        report_path = await create_report(user_id, is_all_time_report)
        document = FSInputFile(report_path)

        await callback.answer("📄 Monthly report sent!")
        await callback.message.answer_document(document=document)
        remove_temp_files(report_path)

    except Exception as e:
        logger.error(f"Error in reports: {e}")
