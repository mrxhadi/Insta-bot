from instabot import Bot
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv
import os

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# تنظیمات اینستاگرام
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")

# تنظیمات تلگرام
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ربات اینستاگرام
insta_bot = Bot()
insta_bot.login(username=INSTA_USERNAME, password=INSTA_PASSWORD)

# دستور شروع در تلگرام
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('سلام! به ربات مدیریت اینستاگرام خوش آمدید.')

# دستور پست کردن عکس در اینستاگرام
def post_photo(update: Update, context: CallbackContext) -> None:
    try:
        # دریافت عکس از کاربر
        photo_file = update.message.photo[-1].get_file()
        photo_path = "temp_photo.jpg"
        photo_file.download(photo_path)

        # پست کردن عکس در اینستاگرام
        insta_bot.upload_photo(photo_path, caption="این یک پست وایرال است!")
        update.message.reply_text("عکس با موفقیت در اینستاگرام پست شد!")
    except Exception as e:
        update.message.reply_text(f"خطا در پست کردن عکس: {e}")

# اجرای ربات تلگرام
def main() -> None:
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("post", post_photo))

    updater.start_polling()
    updater.idle()

if name == 'main':
    print("ربات در حال اجراست...")
    main()
