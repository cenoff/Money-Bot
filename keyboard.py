from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📊 Statistics"),
            KeyboardButton(text="📝 Subscriptions"),
            KeyboardButton(text="📉 Saved"),
        ],
        [
            KeyboardButton(text="🍔 Fast Food"),
            KeyboardButton(text="🍎 Groceries"),
            KeyboardButton(text="🎉 Nightlife"),
        ],
        [
            KeyboardButton(text="🚬 Smoking"),
            KeyboardButton(text="👕 Apparel"),
            KeyboardButton(text="🖥 Electronics"),
        ],
        [
            KeyboardButton(text="💅 Beauty & Care"),
            KeyboardButton(text="🚗 Transport"),
            KeyboardButton(text="🏠 Housing"),
        ],
        [
            KeyboardButton(text="🎁 Gifts"),
            KeyboardButton(text="💸 Debts"),
            KeyboardButton(text="📦 Miscellaneous"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Choose an action or category",
)

category_subscriptions_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ Add Subscription", callback_data="add_subscription"
            )
        ],
        [
            InlineKeyboardButton(
                text="➖ Remove Subscription",
                callback_data="disable_subscriptions_list",
            )
        ],
    ]
)


async def subscriptions_keyboard(
    subscriptions_names: list[str], is_active: bool
) -> InlineKeyboardMarkup:
    callback = "sub_select:" if is_active else "sub_enable:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    row = []

    for i, subscriptions_name in enumerate(subscriptions_names, start=1):
        row.append(
            InlineKeyboardButton(
                text=subscriptions_name,
                callback_data=f"{callback}{subscriptions_name}",
            )
        )
        if i % 3 == 0:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)

    row = []
    row.append(
        InlineKeyboardButton(text="⬅️ Back", callback_data="back_to:subscriptions")
    )
    keyboard.inline_keyboard.append(row)

    return keyboard


reports_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Download monthly report", callback_data="report:month"
            )
        ],
        [
            InlineKeyboardButton(
                text="Download all-time report", callback_data="report:all_time"
            ),
        ],
    ]
)


saving_options = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add savings", callback_data="add_saving")]
    ]
)
