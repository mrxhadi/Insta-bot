import os
import threading
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv

# تنظیم لاگ‌گیری برای دیباگ کردن
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# بارگذاری متغیرهای محیطی
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 8000))  # برای حل مشکل "No open ports found"

if not TELEGRAM_TOKEN:
    raise ValueError("⚠️ لطفاً متغیر `TELEGRAM_TOKEN` را در تنظیمات Render اضافه کنید.")

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

# ایجاد بات تلگرام
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context: CallbackContext) -> None:
    logging.info("دستور /start اجرا شد.")
    await update.message.reply_text("✅ سلام! به ربات مدیریت اینستاگرام خوش آمدید.\nدستورات:\n/start - شروع\n/post - ارسال عکس")

async def post_photo(update: Update, context: CallbackContext) -> None:
    try:
        if not update.message.photo:
            await update.message.reply_text("⚠️ لطفاً یک عکس ارسال کنید.")
            return

        # دریافت فایل عکس
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        # دانلود عکس
        photo_path = "temp_photo.jpg"
        await file.download_to_drive(photo_path)

        logging.info(f"✅ عکس با موفقیت ذخیره شد: {photo_path}")
        await update.message.reply_text(f"✅ عکس با موفقیت ذخیره شد: `{photo_path}`")

        os.remove(photo_path)  # حذف فایل بعد از استفاده

    except Exception as e:
        logging.error(f"⚠️ خطا در پردازش عکس: {e}")
        await update.message.reply_text(f"⚠️ خطا در پردازش عکس: {e}")

# ثبت دستورات ربات
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.PHOTO, post_photo))

logging.info("✅ ربات تلگرام در حال اجراست...")
bot_app.run_polling()
