from instabot import Bot
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
import os
import asyncio

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# تنظیمات اینستاگرام
INSTA_USERNAME = os.getenv("INSTA_USERNAME")  # یوزرنیم اینستاگرام
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")  # پسورد اینستاگرام

# تنظیمات تلگرام
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # توکن ربات تلگرام

# بررسی مقدار متغیرها
if not INSTA_USERNAME or not INSTA_PASSWORD or not TELEGRAM_TOKEN:
    raise ValueError("لطفاً متغیرهای محیطی INSTA_USERNAME، INSTA_PASSWORD و TELEGRAM_TOKEN را تنظیم کنید.")

# ورود به اینستاگرام
insta_bot = Bot()
insta_bot.login(username=INSTA_USERNAME, password=INSTA_PASSWORD)

# دستور /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('سلام! به ربات مدیریت اینستاگرام خوش آمدید.')

# دستور /post برای ارسال عکس به اینستاگرام
async def post_photo(update: Update, context: CallbackContext) -> None:
    try:
        if not update.message.photo:
            await update.message.reply_text("لطفاً یک عکس ارسال کنید.")
            return
        
        # دریافت عکس از تلگرام
        photo_file = await update.message.photo[-1].get_file()
        photo_path = "temp_photo.jpg"
        await photo_file.download(photo_path)

        # ارسال عکس به اینستاگرام
        insta_bot.upload_photo(photo_path, caption="این یک پست وایرال است!")
        await update.message.reply_text("✅ عکس با موفقیت در اینستاگرام پست شد!")

        # حذف فایل موقت
        os.remove(photo_path)
        os.remove(photo_path + ".REMOVE_ME")
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در پست کردن عکس: {e}")

# راه‌اندازی ربات تلگرام
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, post_photo))

    print("✅ ربات تلگرام اجرا شد...")
    app.run_polling()

# اجرای برنامه
if name == 'main':
    main()
