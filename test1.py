import json
from datetime import datetime
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os

# متغیرهای محیطی
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ربات تلگرام
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# وب‌اپ Flask
flask_app = Flask(__name__)

# متغیرها برای ذخیره حالت کاربر و داده‌ها
user_states = {}
user_data = {}

# مسیر وب‌هوک
@flask_app.route("/", methods=["POST"])
def webhook():
    json_data = request.get_json()
    update = Update.de_json(json_data, telegram_app.bot)
    telegram_app.process_update(update)
    return "OK"

# تابع ذخیره داده‌ها در فایل JSON
def save_to_file(data):
    with open("user_data.json", "w") as file:
        json.dump(data, file, indent=4)

# تابع تبدیل تاریخ تولد به سن
def calculate_age(birthdate):
    today = datetime.today()
    birthdate = datetime.strptime(birthdate, "%Y-%m-%d")
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

# تابع محاسبه امتیاز
def calculate_score(data):
    age = data.get("age")
    education_score = {"دیپلم": 10, "کاردانی": 10, "کارشناسی": 15, "کارشناسی ارشد": 15, "دکتری": 20}.get(data.get("education"), 0)
    language_score = {"ضعیف (پایینتر از B1)": 0, "متوسط (‌‌B1 و B2)": 10, "قوی (بالاتر از B2)": 20}.get(data.get("language"), 0)
    return age + education_score + language_score

# پاسخ به دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["ویزای Skilled-Worker", "ویزای تحصیلی"], ["ویزای خانواده"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    user_id = str(update.message.chat_id)
    user_states[user_id] = None
    user_data[user_id] = {}
    await update.message.reply_text("سلام! من ربات خدمات مهاجرت هستم. چطور می‌تونم کمک کنم؟", reply_markup=reply_markup)

# مدیریت پاسخ‌های کاربر
async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # کد مدیریت ورودی‌ها مانند قبل
    pass

# افزودن هندلرها به ربات
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))

# اجرای Flask
if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=5000)
