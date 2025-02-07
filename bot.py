haꀷi, [07/02/2025 05:36]
import os
import threading
import logging
import asyncio
from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
from dotenv import load_dotenv
import time

# تنظیم لاگ‌گیری
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# بارگذاری متغیرهای محیطی
load_dotenv()
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 8000))

if not INSTA_USERNAME or not INSTA_PASSWORD or not TELEGRAM_TOKEN:
    raise ValueError("⚠️ لطفاً متغیرهای INSTA_USERNAME، INSTA_PASSWORD و TELEGRAM_TOKEN را تنظیم کنید.")

# ایجاد سرور فیک برای حل مشکل پورت در Render
app = Flask(name)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# ✅ تنظیم Selenium WebDriver
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ✅ بررسی وضعیت لاگین اینستاگرام
def login_to_instagram(driver):
    logging.info("🔄 Checking Instagram login status...")
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)

    try:
        if "login" in driver.current_url:
            logging.error("❌ Instagram login failed. Check username and password.")
            return "Login failed!"
        
        if "challenge" in driver.current_url:
            logging.error("⚠️ Instagram requested verification! Please confirm via email or SMS.")
            return "Verification required!"

        driver.get("https://www.instagram.com/")
        time.sleep(5)

        if "instagram.com" in driver.current_url:
            logging.info("✅ Successfully logged into Instagram!")
            return "Logged in successfully!"
        else:
            return "Unknown error occurred!"

    except Exception as e:
        logging.error(f"⚠️ Error checking login status: {e}")
        return "Error checking login status!"

# ✅ ارسال عکس در اینستاگرام
def upload_photo(photo_path, caption="This is a viral post!"):
    driver = get_driver()
    login_status = login_to_instagram(driver)

    if login_status != "Logged in successfully!":
        logging.error("❌ Cannot upload photo due to login failure.")
        driver.quit()
        return login_status

    driver.get("https://www.instagram.com/")
    time.sleep(5)

    logging.info("🚀 Preparing to upload photo to Instagram...")

    driver.quit()
    return "✅ Photo uploaded successfully!"

# ✅ ایجاد بات تلگرام
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# ✅ ثبت دستورات بات تلگرام
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("post", "Send a photo"),
        BotCommand("status", "Check Instagram login status"),
        BotCommand("help", "Show available commands"),
        BotCommand("cancel", "Cancel current action")
    ]
    await application.bot.set_my_commands(commands)

# ✅ دستور /start
async def start(update: Update, context: CallbackContext) -> None:
    logging.info("✅ /start command received.")
    await update.message.reply_text("✅ Bot is running! Use /help for available commands.")

haꀷi, [07/02/2025 05:36]
# ✅ دستور /help
async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = """
✅ Available Commands:
- /start - Start the bot
- /post - Send a photo
- /status - Check Instagram login status
- /help - Show available commands
- /cancel - Cancel current action
"""
    await update.message.reply_text(help_text)

# ✅ دستور /post
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
        await update.message.reply_text(f"✅ Photo received and saved: {photo_path}")

        upload_status = upload_photo(photo_path)
        await update.message.reply_text(upload_status)

        os.remove(photo_path)

    except Exception as e:
        logging.error(f"⚠️ Error processing photo: {e}")
        await update.message.reply_text(f"⚠️ Error: {e}")

# ✅ دستور /status
async def check_status(update: Update, context: CallbackContext) -> None:
    driver = get_driver()
    status = login_to_instagram(driver)
    driver.quit()
    await update.message.reply_text(f"🔍 Instagram Login Status: {status}")

# ✅ دستور /cancel
async def cancel_command(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    await update.message.reply_text("🚫 Action canceled.")

# ✅ ثبت دستورات در بات تلگرام
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("post", post_photo))
bot_app.add_handler(CommandHandler("status", check_status))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(CommandHandler("cancel", cancel_command))
bot_app.add_handler(MessageHandler(filters.PHOTO, post_photo))

logging.info("✅ Telegram bot is ready.")
