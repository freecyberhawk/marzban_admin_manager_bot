from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup


class BotKeyboard:

    @staticmethod
    def get_main_menu(super_user: bool):
        keyboard = [
            [KeyboardButton("📦 ساخت اشتراک")],
            [KeyboardButton("👥 مدیریت کاربران")],
        ]

        if super_user:
            keyboard[1].append(KeyboardButton("👮🏻‍♂️ مدیریت ادمین"))
            # keyboard.append([KeyboardButton("⚙️ تنظیمات پنل")])
        else:
            keyboard[1].append(KeyboardButton("💰 کیف پول من"))

        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    @staticmethod
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

    @staticmethod
    def admins_management_menu():
        keyboard = [
            [
                InlineKeyboardButton("جستجو ادمین", callback_data="create_subscription_action_duration:1"),
                InlineKeyboardButton("ساخت ادمین", callback_data="create_admin"),
            ],
            [
                InlineKeyboardButton("لیست ادمین ها", callback_data="create_subscription_action_duration:3"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
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

    @staticmethod
    def show_user_list_menu(users, page, total_pages):
        keyboard = []
        row = []
        for i, user in enumerate(users, 1):
            if user.status == 'active':
                user_status = '✅'
            elif user.status == 'limited':
                user_status = ''
            elif user.status == 'disabled':
                user_status = ''
            elif user.status == 'onhold':
                user_status = '✅'
            else:
                user_status = ''  # expired

            row.append(InlineKeyboardButton(f"{user.username} {user_status}",
                                            callback_data="create_subscription_action_size:50"))
            if i % 2 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        if total_pages > 1:
            if page < total_pages:
                keyboard.append([InlineKeyboardButton(
                    text="صفحه بعد",
                    callback_data=f'users:{page + 1}'
                )])

            if page > 1:
                keyboard.append([InlineKeyboardButton(
                    text="صفحه قبل",
                    callback_data=f'users:{page - 1}'
                )])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def wallet_menu():
        keyboard = [
            [
                InlineKeyboardButton("📜 لیست تراکنش‌ها", callback_data="create_subscription_action_duration:3"),
                InlineKeyboardButton("💵 افزایش موجودی", callback_data="create_subscription_action_duration:3"),
            ],
        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def cancel():
        return InlineKeyboardMarkup([[InlineKeyboardButton("انصراف", callback_data="cancel")]])

    @staticmethod
    def confirm_create_admin():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(" تایید نهایی", callback_data="confirm_create_admin")],
            [InlineKeyboardButton("انصراف", callback_data="cancel")]
        ])
