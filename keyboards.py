from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu(super_user: bool):
    keyboard = [
        [KeyboardButton("📦 ساخت اشتراک")],
        [KeyboardButton("👥 مدیریت کاربران")],
        [
            KeyboardButton("⚡️ آی پی ثابت"),
            KeyboardButton("🌎 سرورهای موجود")
        ],
    ]

    if super_user:
        keyboard[1].append(KeyboardButton("👮🏻‍♂️ مدیریت ادمین"))
        keyboard.append([KeyboardButton("⚙️ تنظیمات پنل")])
    else:
        keyboard[1].append(KeyboardButton("💰 کیف پول من"))

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_the_duration_of_packets():
    keyboard = [
        [
            InlineKeyboardButton("۳ ماهه", callback_data="create_subscription_action_duration:3"),
            InlineKeyboardButton("۱ ماهه", callback_data="create_subscription_action_duration:1"),

        ],
        [
            InlineKeyboardButton("۶ ماهه", callback_data="create_subscription_action_duration:6")
        ],
        [
            InlineKeyboardButton("دوره دلخواه", callback_data="create_subscription_action_duration:x")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_the_size_of_packets():
    keyboard = [
        [
            InlineKeyboardButton("۵۰ گیگ", callback_data="create_subscription_action_size:50"),
            InlineKeyboardButton("۳۰ گیگ", callback_data="create_subscription_action_size:30")
        ],
        [
            InlineKeyboardButton("۸۰ گیگ", callback_data="create_subscription_action_size:80")
        ],
        [
            InlineKeyboardButton("حجم دلخواه", callback_data="create_subscription_action_size:x")
        ],
        [
            InlineKeyboardButton("بازگشت", callback_data="create_subscription_action_size:back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
