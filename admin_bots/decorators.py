from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from dep.db import GetDB  # update path if needed

from dep.db.crud import get_admin_by_telegram_id


def permission_required(admin=False, superuser=False):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            if update.effective_user:
                user_id = update.effective_user.id
            else:
                # Handle gracefully or skip
                print("No user info found in this update.")
                return

            try:
                # Open sync DB session inside async context (if using async SQLAlchemy, adapt accordingly)
                with GetDB() as db:
                    admin_obj = get_admin_by_telegram_id(db, user_id)

                    if not admin_obj:
                        await update.message.reply_text("🚫 دسترسی غیرمجاز: شما ادمین نیستید.")
                        return

                    if superuser and not admin_obj.is_sudo:
                        await update.message.reply_text("🚫 فقط سوپر یوزرها اجازه دارند.")
                        return

                    if admin and not admin_obj:
                        await update.message.reply_text("🚫 فقط ادمین‌ها اجازه دارند.")
                        return

            except Exception as e:
                await update.message.reply_text("⚠️ خطایی در بررسی دسترسی رخ داد.")
                return

            # Passed all checks
            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator
