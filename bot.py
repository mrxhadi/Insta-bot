import os

# تنظیم دستی یک مقدار برای PORT تا Render به مشکل نخوره
os.environ["PORT"] = "8000"

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

# بارگذاری متغیرهای محیطی
load_dotenv()

INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not INSTA_USERNAME or not INSTA_PASSWORD or not TELEGRAM_TOKEN:
    raise ValueError("لطفاً متغیرهای محیطی را تنظیم کنید.")

# راه‌اندازی Selenium با شبیه‌سازی نسخه موبایل
def get_driver():
    options = webdriver.ChromeOptions()
    mobile_emulation = {
        "deviceMetrics": {"width": 360, "height": 640, "pixelRatio": 3.0},
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.104 Mobile Safari/537.36"
    }
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ورود به اینستاگرام
def login_to_instagram(driver):
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)

    username_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
    password_input = driver.find_element(By.NAME, "password")

    username_input.send_keys(INSTA_USERNAME)
    password_input.send_keys(INSTA_PASSWORD)
    password_input.send_keys(Keys.RETURN)
    
    time.sleep(10)

# ارسال عکس در اینستاگرام
def upload_photo(photo_path, caption="این یک پست وایرال است!"):
    driver = get_driver()
    login_to_instagram(driver)

    driver.get("https://www.instagram.com/")
    time.sleep(5)

    try:
        upload_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='menuitem']"))
        )
        upload_button.click()
        time.sleep(3)

        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )
        file_input.send_keys(os.path.abspath(photo_path))
        time.sleep(3)

        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Next']"))
        )
        next_button.click()
        time.sleep(3)

        caption_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "textarea"))
        )
        caption_area.send_keys(caption)
        time.sleep(2)

        share_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Share']"))
        )
        share_button.click()
        time.sleep(5)

        print("✅ عکس با موفقیت در اینستاگرام پست شد!")
    
    except Exception as e:
        print(f"⚠️ خطا در ارسال پست: {e}")
    
    driver.quit()

# دستور `/start`
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('سلام! به ربات مدیریت اینستاگرام خوش آمدید.')

# دستور `/post` برای ارسال عکس
async def post_photo(update: Update, context: CallbackContext) -> None:
    try:
        if not update.message.photo:
            await update.message.reply_text("لطفاً یک عکس ارسال کنید.")
            return

        photo_file = await update.message.photo[-1].get_file()
        photo_path = "temp_photo.jpg"
        await photo_file.download(photo_path)

        upload_photo(photo_path, caption="این یک پست وایرال است!")
        await update.message.reply_text("✅ عکس با موفقیت در اینستاگرام پست شد!")

        os.remove(photo_path)

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در پست کردن عکس: {e}")

# راه‌اندازی ربات تلگرام
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, post_photo))

    print("✅ ربات تلگرام اجرا شد...")
    app.run_polling()

if __name__ == '__main__':
    main()
