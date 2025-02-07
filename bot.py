import os
import threading
import logging
from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
import time

# تنظیم لاگ‌گیری برای بررسی مشکلات
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# بارگذاری متغیرهای محیطی
load_dotenv()

INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 8000))  # حل مشکل "No open ports found"

if not INSTA_USERNAME or not INSTA_PASSWORD or not TELEGRAM_TOKEN:
    raise ValueError("⚠️ لطفاً متغیرهای محیطی `INSTA_USERNAME`، `INSTA_PASSWORD` و `TELEGRAM_TOKEN` را در تنظیمات Render اضافه کنید.")

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

# تنظیم Selenium WebDriver
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # بدون باز شدن مرورگر
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ورود به اینستاگرام و بررسی وضعیت لاگین
def login_to_instagram(driver):
    logging.info("🔄 در حال ورود به اینستاگرام...")
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)

    username_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
    password_input = driver.find_element(By.NAME, "password")

    username_input.send_keys(INSTA_USERNAME)
    password_input.send_keys(INSTA_PASSWORD)
    password_input.send_keys(Keys.RETURN)

    time.sleep(10)  # صبر برای ورود

    # بررسی اینکه آیا ورود موفق بوده
    current_url = driver.current_url
    if "challenge" in current_url:
        logging.error("⚠️ اینستاگرام درخواست تأیید (Challenge) داده! لطفاً ورود را از طریق ایمیل یا پیامک تأیید کنید.")
    elif "login" in current_url:
        logging.error("❌ ورود به اینستاگرام ناموفق بود. لطفاً یوزرنیم و پسورد را بررسی کنید.")
    else:
        logging.info("✅ ورود به اینستاگرام موفقیت‌آمیز بود!")

# دستور `/start`
async def start(update: Update, context: CallbackContext) -> None:
    logging.info("✅ دستور /start اجرا شد.")
    await update.message.reply_text("✅ سلام! به ربات مدیریت اینستاگرام خوش آمدید.\nدستورات:\n/start - شروع\n/post - ارسال عکس")

# دستور `/post` برای ارسال عکس
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

        # ورود به اینستاگرام و آپلود عکس
        driver = get_driver()
        login_to_instagram(driver)

        # اینجا می‌تونی کد آپلود به اینستاگرام رو اضافه کنی
        logging.info("🚀 آماده برای آپلود عکس به اینستاگرام...")

        driver.quit()
        os.remove(photo_path)  # حذف فایل بعد از استفاده

    except Exception as e:
        logging.error(f"⚠️ خطا در پردازش عکس: {e}")
        await update.message.reply_text(f"⚠️ خطا در پردازش عکس: {e}")

# ایجاد بات تلگرام
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.PHOTO, post_photo))

logging.info("✅ ربات تلگرام در حال اجراست...")
bot_app.run_polling()
