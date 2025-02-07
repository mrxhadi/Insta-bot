import os
import threading
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext

# تنظیم لاگ‌گیری برای بررسی خطاها
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# بارگذاری متغیرهای محیطی
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 8000))  # برای حل مشکل No open ports found

if not TELEGRAM_TOKEN:
    raise ValueError("⚠️ لطفاً متغیر `TELEGRAM_TOKEN` را تنظیم کنید.")

# ایجاد سرور فیک برای حل مشکل پورت در Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# اجرای Flask در یک Thread جداگانه
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# ایجاد بات تلگرام با جلوگیری از پیام‌های تکراری
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# ✅ مدیریت خطاها (برای حل ارور No error handlers are registered)
async def error_handler(update: object, context: CallbackContext) -> None:
    logging.error(f"⚠️ Exception: {context.error}")

# دستور `/start`
async def start(update: Update, context: CallbackContext) -> None:
    logging.info("✅ /start command received.")
    await update.message.reply_text("✅ Welcome! Use /help to see available commands.")

# دستور `/help`
async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = """
✅ Available Commands:
- /start - Start the bot
- /post - Send a photo
- /help - Show all commands
"""
    await update.message.reply_text(help_text)

# دستور `/post`
async def post_photo(update: Update, context: CallbackContext) -> None:
    try:
        if not update.message.photo:
            await update.message.reply_text("⚠️ Please send a photo.")
            return

        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        photo_path = "temp_photo.jpg"
        await file.download_to_drive(photo_path)

        logging.info(f"✅ Photo saved: {photo_path}")
        await update.message.reply_text(f"✅ Photo received and saved: `{photo_path}`")

        os.remove(photo_path)

    except Exception as e:
        logging.error(f"⚠️ Error processing photo: {e}")
        await update.message.reply_text(f"⚠️ Error: {e}")

# ثبت دستورات و مدیریت خطاها
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(MessageHandler(filters.PHOTO, post_photo))
bot_app.add_error_handler(error_handler)

logging.info("✅ Telegram bot is running...")

# ✅ جلوگیری از پیام‌های تکراری و اجرای Polling
bot_app.run_polling(drop_pending_updates=True)
