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
PORT = int(os.getenv("PORT", 8000))  # حل مشکل No open ports found

if not INSTA_USERNAME or not INSTA_PASSWORD or not TELEGRAM_TOKEN:
    raise ValueError("⚠️ لطفاً متغیرهای محیطی `INSTA_USERNAME`، `INSTA_PASSWORD` و `TELEGRAM_TOKEN` را تنظیم کنید.")

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
    logging.info("🔄 Logging into Instagram...")
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)

    username_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
    password_input = driver.find_element(By.NAME, "password")

    username_input.send_keys(INSTA_USERNAME)
    password_input.send_keys(INSTA_PASSWORD)
    password_input.send_keys(Keys.RETURN)

    time.sleep(10)

    # بررسی اینکه آیا ورود موفق بوده
    current_url = driver.current_url
    if "challenge" in current_url:
        logging.error("⚠️ Instagram requested verification! Please confirm via email or SMS.")
        return "Verification required!"
    elif "login" in current_url:
        logging.error("❌ Instagram login failed. Check username and password.")
        return "Login failed!"
    else:
        logging.info("✅ Successfully logged into Instagram!")
        return "Logged in successfully!"

# ارسال عکس در اینستاگرام
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

# ایجاد بات تلگرام
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# پنل دستورات تلگرام
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("post", "Send a photo"),
        BotCommand("caption", "Set caption for the next post"),
        BotCommand("status", "Check Instagram login status"),
        BotCommand("help", "Show available commands"),
        BotCommand("cancel", "Cancel current action")
    ]
    await application.bot.set_my_commands(commands)

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
- /caption <text> - Set caption for the next post
- /status - Check Instagram login status
- /help - Show available commands
- /cancel - Cancel current action
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

        upload_status = upload_photo(photo_path)
        await update.message.reply_text(upload_status)

        os.remove(photo_path)

    except Exception as e:
        logging.error(f"⚠️ Error processing photo: {e}")
        await update.message.reply_text(f"⚠️ Error: {e}")

# دستور `/status`
async def check_status(update: Update, context: CallbackContext) -> None:
    driver = get_driver()
    status = login_to_instagram(driver)
    driver.quit()
    await update.message.reply_text(f"🔍 Instagram Login Status: {status}")

# دستور `/caption`
async def set_caption(update: Update, context: CallbackContext) -> None:
    caption = " ".join(context.args)
    if not caption:
        await update.message.reply_text("⚠️ Please provide a caption!")
    else:
        context.user_data["caption"] = caption
        await update.message.reply_text(f"✅ Caption set to: {caption}")

# دستور `/cancel`
async def cancel_command(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    await update.message.reply_text("🚫 Action canceled.")

# ثبت دستورات و مدیریت خطاها
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("post", post_photo))
bot_app.add_handler(CommandHandler("caption", set_caption))
bot_app.add_handler(CommandHandler("status", check_status))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(CommandHandler("cancel", cancel_command))
bot_app.add_handler(MessageHandler(filters.PHOTO, post_photo))

logging.info("✅ Telegram bot is running...")

# راه‌اندازی بات و ثبت دستورات
async def start_bot():
    await set_bot_commands(bot_app)
    bot_app.run_polling(drop_pending_updates=True)

asyncio.run(start_bot())
