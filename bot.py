import os
import threading
import logging
import asyncio
from flask import Flask
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
from dotenv import load_dotenv

# تنظیم لاگ‌گیری برای بررسی مشکلات
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# بارگذاری متغیرهای محیطی
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 8000))

if not TELEGRAM_TOKEN:
    raise ValueError("⚠️ لطفاً متغیر TELEGRAM_TOKEN را در تنظیمات Render اضافه کنید.")

# ایجاد سرور فیک برای حل مشکل پورت در Render
app = Flask(name)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# اجرای Flask در یک Thread جداگانه
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# ✅ ایجاد بات تلگرام
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# ✅ دستور /start
async def start(update: Update, context: CallbackContext) -> None:
    logging.info("✅ /start command received.")
    await update.message.reply_text("✅ Bot is running! Use /help for available commands.")

# ✅ دستور /help
async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = """
✅ Available Commands:
- /start - Start the bot
- /help - Show available commands
"""
    await update.message.reply_text(help_text)

# ✅ ثبت دستورات
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))

logging.info("✅ Bot handlers registered successfully.")

# ✅ اجرای بات با مدیریت asyncio بدون ایجاد مشکل Loop
async def start_bot():
    try:
        await bot_app.bot.set_my_commands([
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show available commands")
        ])
        logging.info("✅ Bot commands set successfully.")
        
        while True:
            logging.info("✅ Bot is running and waiting for messages...")
            await bot_app.run_polling(drop_pending_updates=True)
            await asyncio.sleep(1)
    except Exception as e:
        logging.error(f"⚠️ Bot encountered an error: {e}")
        await asyncio.sleep(5)
        await start_bot()  # اجرای مجدد در صورت بروز خطا

# ✅ حل مشکل Loop: اجرای بات با asyncio.run()
if __name__ == "__main__":
    asyncio.run(start_bot())
