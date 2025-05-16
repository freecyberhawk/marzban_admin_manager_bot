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
        BotCommand("start", "Show main"),
        BotCommand("scan", "Print IPs"),
    ]
    await application.bot.set_my_commands(commands)


# First menu
def get_main_menu():
    keyboard = [
        [KeyboardButton("📦 ساخت اشتراک")],
        [KeyboardButton("👥 مدیریت کاربران"), KeyboardButton("💰 موجودی کیف پول")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


# Second menu
def get_second_menu():
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)


# Access control check
def is_authorized(user_id: int) -> bool:
    return user_id in AUTHORIZED_USERS_ID


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

    await update.message.reply_text(
        f"✅ Welcome, {full_name}!\nYour ID: {user_id}",
        reply_markup=get_main_menu()
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
        await query.edit_message_text("📋 You are in the second menu.", reply_markup=get_second_menu())
    elif query.data == "main_menu":
        await query.edit_message_text("🏠 Back to the main menu.", reply_markup=get_main_menu())


# Catch all text messages
async def all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔️ You are not authorized to use this bot.")
        return

    # Echo the message
    await update.message.reply_text(f"You said: {update.message.text}", reply_markup=get_main_menu())


# Main entry point
def main():
    # import asyncio

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL, all_messages))  # Capture any message
    # asyncio.run(set_commands(app))
    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
