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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
from dotenv import load_dotenv
import time

# Logging setup
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Load environment variables
load_dotenv()

INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.getenv("PORT", 8000))  # Fix "No open ports found" error

if not INSTA_USERNAME or not INSTA_PASSWORD or not TELEGRAM_TOKEN:
    raise ValueError("⚠️ Please set `INSTA_USERNAME`, `INSTA_PASSWORD`, and `TELEGRAM_TOKEN` in Render settings.")

# Flask fake server to bypass Render's open port requirement
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Selenium WebDriver setup
def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Instagram login and status check
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

    # Check login status
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

# Telegram bot setup
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Command: /start with inline buttons
async def start(update: Update, context: CallbackContext) -> None:
    logging.info("✅ /start command received.")
    keyboard = [
        [InlineKeyboardButton("📸 Upload Photo", callback_data="upload")],
        [InlineKeyboardButton("🔍 Check Status", callback_data="status")],
        [InlineKeyboardButton("❓ Help", callback_data="help")],
        [InlineKeyboardButton("🚫 Cancel", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ Welcome! Use the buttons below:", reply_markup=reply_markup)

# Command: /post (upload photo)
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

# Command: /caption (set caption)
async def set_caption(update: Update, context: CallbackContext) -> None:
    caption = " ".join(context.args)
    if not caption:
        await update.message.reply_text("⚠️ Please provide a caption!")
    else:
        context.user_data["caption"] = caption
        await update.message.reply_text(f"✅ Caption set to: {caption}")

# Command: /status (check Instagram login status)
async def check_status(update: Update, context: CallbackContext) -> None:
    driver = get_driver()
    status = login_to_instagram(driver)
    driver.quit()
    await update.message.reply_text(f"🔍 Instagram Login Status: {status}")

# Command: /help (show available commands)
async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = """
✅ Available Commands:
- /start - Start the bot
- /post - Send a photo
- /caption <text> - Set caption for the next post
- /status - Check Instagram login status
- /cancel - Cancel current action
"""
    await update.message.reply_text(help_text)

# Command: /cancel (cancel operation)
async def cancel_command(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    await update.message.reply_text("🚫 Action canceled.")

# Inline button handlers
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "upload":
        await query.message.reply_text("📸 Please send a photo to upload.")
    elif query.data == "status":
        await check_status(update, context)
    elif query.data == "help":
        await help_command(update, context)
    elif query.data == "cancel":
        await cancel_command(update, context)

# Register handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("post", post_photo))
bot_app.add_handler(CommandHandler("caption", set_caption))
bot_app.add_handler(CommandHandler("status", check_status))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(CommandHandler("cancel", cancel_command))
bot_app.add_handler(MessageHandler(filters.PHOTO, post_photo))
bot_app.add_handler(CallbackQueryHandler(button_handler))

logging.info("✅ Telegram bot is running...")
bot_app.run_polling()
