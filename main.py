"""
Bot Name: Marzban Admin Manager Bot
Author: @freecyberhawk
GitHub: https://github.com/freecyberhawk

Description:
This Telegram bot is designed to manage users and admins on a Marzban VPN panel.

Features:
- Superusers can:
  • Add or remove admin balances manually.
  • Define custom subscription packages.
  • Approve admin top-up requests by reviewing invoice images.

- Admins can:
  • Manage their own users.
  • Create and renew subscriptions using predefined packages.
  • Submit top-up requests by sending payment receipts.
  • Track wallet balance and see how much is deducted per subscription.

Wallet System:
Each subscription or renewal deducts a specific amount (per GB) from the admin's wallet based on the price set by the superuser.
"""
from asyncio import create_subprocess_shell
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
import os
import jdatetime

from telegram import BotCommand

load_dotenv()  # Load environment variables from .env file

TOKEN = os.getenv("TOKEN")

AUTHORIZED_USERS_ID = list(map(int, os.getenv("AUTHORIZED_USERS_ID", "").split(",")))
SUPER_ADMINS_ID = list(map(int, os.getenv("SUPER_ADMINS_ID", "").split(",")))

if not TOKEN:
    raise ValueError("🚨 TOKEN not found in .env")

if not AUTHORIZED_USERS_ID:
    raise ValueError("🚨 AUTHORIZED_USERS_ID is empty or missing in .env")

if not SUPER_ADMINS_ID:
    raise ValueError("🚨 SUPER_ADMINS_ID is empty or missing in .env")


async def set_commands(application):
    commands = [
        BotCommand("start", "شروع مجدد"),
        BotCommand("create_subscription", "ساخت اشتراک"),
    ]
    await application.bot.set_my_commands(commands)


# Main menu
def get_main_menu(super_user: bool):
    keyboard = [
        [KeyboardButton("📦 ساخت اشتراک")],
        [KeyboardButton("👥 مدیریت کاربران")]
    ]

    if super_user:
        keyboard[1].append(KeyboardButton("👮🏻‍♂️ مدیریت ادمین"))
        keyboard.append([KeyboardButton("⚙️ تنظیمات پنل")])
    else:
        keyboard[1].append(KeyboardButton("💰 کیف پول من"))

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


# Second menu
def get_subscription_packets():
    keyboard = [
        [
            InlineKeyboardButton("سه ماهه", callback_data="create_subscription_action_duration:3"),
            InlineKeyboardButton("یک ماهه", callback_data="create_subscription_action_duration:1"),

        ],
        [
            InlineKeyboardButton("شش ماهه", callback_data="create_subscription_action_duration:6")
        ],
        [
            InlineKeyboardButton("دوره دلخواه", callback_data="create_subscription_action_duration:x")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# Access control check
def is_authorized(user_id: int) -> bool:
    return user_id in AUTHORIZED_USERS_ID


def is_superuser(user_id: int) -> bool:
    return user_id in SUPER_ADMINS_ID


# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔️ You are not authorized to use this bot.")
        return
    user = update.effective_user
    user_id = user.id

    # Access user details
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()

    if not is_authorized(user_id):
        await update.message.reply_text("⛔️ You are not authorized to use this bot.")
        return

    now_jalali = jdatetime.datetime.now().strftime("%Y/%m/%d ⏰ %H:%M")

    welcome_text = (
        f" سلام، {full_name} خوش آمدید!\n\n"
        f"{now_jalali}\n"
        f"----\n"
        f"کاربران فعال:\n"
        f"{'12/52'} عدد\n"
        f"موجودی کیف پول:\n"
        f"{'123,000'} تومان\n\n"
    )
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu(is_superuser(user_id)),
    )


# Handle button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if not is_authorized(user_id):
        await query.answer("⛔️ Unauthorized", show_alert=True)
        return

    await query.answer()
    if query.data == "second_menu":
        await query.edit_message_text("📋 You are in the second menu.", reply_markup=None)

    elif query.data == "main_menu":
        await query.edit_message_text("🏠 Back to the main menu.", reply_markup=None)

    elif query.data.startswith("create_subscription_action_duration:"):
        duration = query.data.split(":")[1]

        if duration == "x":
            await query.edit_message_text("لطفا تعداد ماه دلخواه را وارد کنید (حداکثر 12):")
            context.user_data["awaiting_create_subscription_action_duration"] = True
        else:
            await query.edit_message_text(f"📦 ساخت اشتراک {duration} ماهه آغاز شد...")


async def create_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await update.message.reply_text("⏳ دوره اشتراک را انتخاب کنید:", reply_markup=get_subscription_packets())


# Catch all text messages
async def all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔️ You are not authorized to use this bot.")
        return

    text = update.message.text

    if context.user_data.get("awaiting_create_subscription_action_duration"):
        if text.isdigit():
            context.user_data["awaiting_create_subscription_action_duration"] = False
            duration = int(text)
            await update.message.reply_text(f"📦 ساخت اشتراک {duration} ماهه آغاز شد...")
            # ادامه منطق ساخت اشتراک دلخواه
        else:
            await update.message.reply_text("❌ لطفا فقط عدد وارد کنید (به ماه):")
        return

    elif text == "📦 ساخت اشتراک":
        await create_subscription(update, context)
        return

    elif text == "👥 مدیریت کاربران":
        await update.message.reply_text("🧑‍💼 مدیریت کاربران", reply_markup=None)
        return

    elif text == "💰 موجودی کیف پول":
        await update.message.reply_text("💳 موجودی کیف پول شما: (مقدار تستی)", reply_markup=None)
        return

    await update.message.reply_text(f"شما گفتید: {text}", reply_markup=None)


# Main entry point
def main():
    # import asyncio

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("create_subscription", create_subscription))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL, all_messages))  # Capture any message
    # asyncio.run(set_commands(app))
    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
