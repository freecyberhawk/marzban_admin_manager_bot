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
import math

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
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

from db.crud import get_admin_by_telegram_id
from dep.db import GetDB, crud
from decorators import permission_required
from utils.watermark import set_watermark
from keyboards import BotKeyboard

load_dotenv()  # Load environment variables from .env file

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("🚨 TOKEN not found in .env")


async def init_user_data(context):
    context.user_data["bot_message_ids"] = []
    context.user_data["awaiting_admin"] = False
    context.user_data["awaiting_user"] = False
    context.user_data["awaiting_wallet"] = False


async def send_and_store(update, context, text, reply_markup=None, parse_mode=None):
    chat_id = update.effective_chat.id

    if "bot_message_ids" in context.user_data:
        for msg_id in context.user_data["bot_message_ids"]:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                print(f"❗️خطا در حذف پیام {msg_id}: {e}")
    context.user_data["bot_message_ids"] = []

    sent_message = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )

    context.user_data["bot_message_ids"].append(sent_message.message_id)

    return sent_message


async def set_commands(application):
    commands = [
        BotCommand("start", "شروع مجدد"),
        BotCommand("create_subscription", "ساخت اشتراک"),
    ]
    await application.bot.set_my_commands(commands)


def get_final_confirm():
    keyboard = [
        [
            InlineKeyboardButton("تایید نهایی", callback_data="create_subscription_action_confirm:ok")
        ],
        [
            InlineKeyboardButton("بازگشت", callback_data="create_subscription_action_confirm:back")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def is_superuser(update) -> bool:
    user = update.effective_user
    user_id = user.id
    with GetDB() as db:
        admin_obj = get_admin_by_telegram_id(db, user_id)
    return admin_obj.is_sudo


# /start command
@permission_required(admin=True)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    with GetDB() as db:
        admin_obj = get_admin_by_telegram_id(db, user_id)
        all_users = crud.get_users_count(db)

    now_jalali = jdatetime.datetime.now().strftime("%Y/%m/%d")

    welcome_text = set_watermark((
        f"🎉 خوش آمدید!\n"
        f"📅 تاریخ: {now_jalali}\n"
        f"\n"
        f"👥 تعداد کاربران:\n"
        f"   {all_users:,} نفر\n"
        f"💰 موجودی کیف پول:\n"
        f"   {admin_obj.hakobot_balance:,} تومان\n"
    ))
    await send_and_store(update, context,
                         welcome_text,
                         reply_markup=BotKeyboard.get_main_menu(is_superuser(update)),
                         )


# Handle button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    if query.data.startswith("create_admin"):
        reply_text = set_watermark((
            "نام کاربری ادمین را وارد کنید: (حداقل ۵ حرف)\n."
        ))
        context.user_data["create_admin_step"] = 1
        await query.edit_message_text(reply_text, reply_markup=BotKeyboard.cancel())
        return

    if query.data.startswith("users:"):
        page = int(query.data.split(":")[1])
        with GetDB() as db:
            admin_obj = get_admin_by_telegram_id(db, user_id)
            if admin_obj.is_sudo:
                all_users = crud.get_users_count(db)
            else:
                all_users = crud.get_users_count(db, admin=admin_obj)
            total_pages = math.ceil(all_users / 11)
            users = crud.get_users(db, offset=(page - 1) * 11, limit=11, sort=[crud.UsersSortingOptions["-created_at"]])
            reply_text = set_watermark("""👥 تعداد کاربران: {all_users}
            
✅ فعال
❌ غیرفعال
🕰 اتمام زمان
🪫 اتمام گیگ
🔌 متصل نشده
""".format(page=page, total_pages=total_pages, all_users=all_users))
        await query.edit_message_text(reply_text, reply_markup=BotKeyboard.show_user_list_menu(users=users, page=page,
                                                                                               total_pages=total_pages))
        return

    if query.data.startswith("create_subscription_action_duration:"):
        duration = query.data.split(":")[1]
        context.user_data["buying__selected_duration"] = duration

        if duration == "x":
            await query.edit_message_text(set_watermark(f"لطفا تعداد ماه دلخواه را وارد کنید (حداکثر 12):\n."))
            context.user_data["awaiting_create_subscription_action_duration"] = True
        else:
            await query.edit_message_text(set_watermark(f"💎 حجم مصرف اشتراک را انتخاب کنید:\n."),
                                          reply_markup=BotKeyboard.get_the_size_of_packets())

    elif query.data.startswith("create_subscription_action_size:"):
        size = query.data.split(":")[1]
        context.user_data["buying__selected_size"] = size

        if size == "back":
            await query.edit_message_text(set_watermark("⏳ دوره اشتراک را انتخاب کنید:\n."),
                                          reply_markup=BotKeyboard.get_the_duration_of_packets())
        elif size == "x":
            await query.edit_message_text(
                set_watermark("لطفا حجم دلخواه را به گیگابایت وارد کنید (حداکثر ۲۰۰ گیگ):\n."))
            context.user_data["awaiting_create_subscription_action_size"] = True
        else:
            cart_packet = (
                f"مشخصات نهایی اشتراک\n"
                f"دوره اشتراک: {context.user_data['buying__selected_duration']} ماهه\n"
                f"حجم مصرف: {context.user_data['buying__selected_size']} گیگابایت\n"
                f"مبلغ سفارش: 12,200 تومان\n"
            )
            await query.edit_message_text(set_watermark(cart_packet), reply_markup=get_final_confirm())

    elif query.data.startswith("create_subscription_action_confirm:"):
        status = query.data.split(":")[1]
        if status == "ok":
            await query.edit_message_text('OK', reply_markup=None)
        else:
            await query.edit_message_text(set_watermark(f"💎 حجم مصرف اشتراک را انتخاب کنید:\n."),
                                          reply_markup=BotKeyboard.get_the_size_of_packets())


async def create_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await update.message.reply_text(set_watermark("⏳ دوره اشتراک را انتخاب کنید:\n."),
                                           reply_markup=BotKeyboard.get_the_duration_of_packets())


async def handle_payment_review_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: CallbackQuery = update.callback_query
    await query.answer()  # بستن لودینگ دکمه

    data = query.data
    action, user_id = data.split(":")

    if action == "approve":
        await query.edit_message_caption(
            caption="✅ رسید پرداخت تأیید شد.\nبا تشکر از شما!",
            reply_markup=None
        )
        # ارسال پیام خاص به بات یا کاربر
        await context.bot.send_message(chat_id=user_id, text="🎉 پرداخت شما تأیید شد.")
    elif action == "reject":
        await query.edit_message_caption(
            caption="❌ رسید پرداخت رد شد.",
            reply_markup=None
        )
        await context.bot.send_message(chat_id=user_id, text="⛔ پرداخت شما تأیید نشد. لطفاً دوباره تلاش کنید.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if context.user_data.get("awaiting_send_image"):
    user = update.effective_user
    with GetDB() as db:
        admin_obj = get_admin_by_telegram_id(db, user.id)
    photo = update.message.photo[-1]  # بهترین کیفیت

    caption = (
        f"📸 رسید پرداخت ارسال شده توسط:\n"
        f"👤 {user.full_name} \n"
        f"({admin_obj.username or 'بدون_نام_کاربری'})\n\n"
        f"لطفاً رسید را بررسی و وضعیت را مشخص کنید 👇"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید", callback_data=f"approve:{user.id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject:{user.id}")
        ]
    ])

    await context.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=photo.file_id,
        caption=caption,
        reply_markup=keyboard
    )

    context.user_data["awaiting_send_image"] = False
    await update.message.reply_text("✅ رسید پرداخت برای بررسی ارسال شد.")


# Catch all text messages
@permission_required(admin=True)
async def all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if context.user_data.get("create_admin_step"):
        if context.user_data.get("create_admin_step") == 1:
            context.user_data["create_admin_step"] = 2
            await send_and_store(update, context, f"چت آی دی ادمین را وارد کنید:",
                                 reply_markup=BotKeyboard.cancel())
            return
        elif context.user_data.get("create_admin_step") == 2:
            context.user_data["create_admin_step"] = 3
            await send_and_store(update, context, f"موجودی کیف پول را وارد کنید: (تومان):",
                                 reply_markup=BotKeyboard.cancel())
            return
        elif context.user_data.get("create_admin_step") == 3:
            context.user_data["create_admin_step"] = 4
            await send_and_store(update, context, f"تعرفه هر گیگ ادمین را وارد کنید: (تومان)",
                                 reply_markup=BotKeyboard.cancel())
            return
        elif context.user_data.get("create_admin_step") == 4:
            context.user_data["create_admin_step"] = 0
            await send_and_store(update, context, f"آیا از ساخت این ادمین اطمینان دارید؟",
                                 reply_markup=BotKeyboard.confirm_create_admin())
            return

    if context.user_data.get("awaiting_create_subscription_action_duration"):
        if text.isdigit():
            context.user_data["awaiting_create_subscription_action_duration"] = False
            duration = text
            context.user_data["buying__selected_duration"] = duration
            await update.message.reply_text(f"💎 حجم مصرف اشتراک را انتخاب کنید:",
                                            reply_markup=BotKeyboard.get_the_size_of_packets())
        else:
            await update.message.reply_text("❌ لطفا فقط عدد وارد کنید (به ماه):")
        return

    if context.user_data.get("awaiting_create_subscription_action_size"):
        if text.isdigit():
            context.user_data["awaiting_create_subscription_action_size"] = False
            size = int(text)
            context.user_data["buying__selected_size"] = size
            cart_packet = (
                f"مشخصات نهایی اشتراک\n"
                f"دوره اشتراک: {context.user_data['buying__selected_duration']} ماهه\n"
                f"حجم مصرف: {context.user_data['buying__selected_size']} گیگابایت\n"
                f"مبلغ سفارش: 12,200 تومان\n"
            )
            await update.message.reply_text(cart_packet, reply_markup=get_final_confirm())
        else:
            await update.message.reply_text("❌ لطفا فقط عدد وارد کنید (به گیگابایت):")
        return


    elif text == "📦 ساخت اشتراک":
        await create_subscription(update, context)
        return

    elif text == "👥 مدیریت کاربران":
        page = 1
        with GetDB() as db:
            total_pages = math.ceil(crud.get_users_count(db) / 11)
            users = crud.get_users(db, offset=(page - 1) * 11, limit=11, sort=[crud.UsersSortingOptions["-created_at"]])

        await update.message.reply_text(set_watermark((
            f"یک کاربر را انتخاب کنید:\n."
        )), reply_markup=BotKeyboard.show_user_list_menu(users=users, page=page, total_pages=total_pages))
        return

    elif text == "💰 کیف پول من":
        user_id = update.message.from_user.id
        with GetDB() as db:
            admin_obj = get_admin_by_telegram_id(db, user_id)
        reply_text = set_watermark((
            f"موجودی:\n"
            f"{admin_obj.hakobot_balance:,} تومان\n"
            f"تعرفه گیگ:\n"
            f"{admin_obj.hakobot_gb_fee:,} تومان\n."
        ))

        await update.message.reply_text(reply_text, reply_markup=BotKeyboard.wallet_menu())
        return

    elif text == "👮🏻‍♂️ مدیریت ادمین":

        admin_status_data = set_watermark(
            (
                f"اطلاعات ادمین ها :\n"
                f"\n"
                f"✅ ادمین فعال: 12/33 \n"
                f"\n"
                f"💎 گیگ مصرفی: 120 گیگابایت \n"
            )
        )
        await update.message.reply_text(admin_status_data, reply_markup=BotKeyboard.admins_management_menu())
        return

    await update.message.reply_text(f"جستجوی کاربر: {text}", reply_markup=None)


# Main entry point
def main():
    # import asyncio

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("create_subscription", create_subscription))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(handle_payment_review_callback))
    app.add_handler(MessageHandler(filters.ALL, all_messages))  # Capture any message

    # asyncio.run(set_commands(app))
    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
