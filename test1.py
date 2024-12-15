import json
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from flask import Flask, request

app = Flask(__name__)

# ربات تلگرام
BOT_TOKEN = 8099865863:AAHxaeulviM5E5tlpB-cQiol9bymdlj8Cr0
application = ApplicationBuilder().token(BOT_TOKEN).build()

@app.route("/", methods=["POST"])
def webhook():
    json_data = request.get_json()
    update = Update.de_json(json_data, application.bot)
    application.process_update(update)
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    
# متغیرها برای ذخیره حالت کاربر و داده‌ها
user_states = {}
user_data = {}

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
    # محاسبه امتیاز سن
    age = data.get("age")
    if age <= 17:
        age_score = 0
    elif 18 <= age <= 24:
        age_score = 25
    elif 25 <= age <= 32:
        age_score = 30
    elif 33 <= age <= 39:
        age_score = 25
    elif 40 <= age <= 44:
        age_score = 15
    else:
        age_score = 0

    # امتیاز مدرک تحصیلی
    education_score = {
        "دیپلم": 10,
        "کاردانی": 10,
        "کارشناسی": 15,
        "کارشناسی ارشد": 15,
        "دکتری": 20
    }.get(data.get("education"), 0)

    # امتیاز سطح زبان
    language_score = {
        "ضعیف (پایینتر از B1)": 0,
        "متوسط (‌‌B1 و B2)": 10,
        "قوی (بالاتر از B2)": 20
    }.get(data.get("language"), 0)

    return age_score + education_score + language_score

# پاسخ به دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # گزینه‌های پیشنهادی برای کاربر
    keyboard = [
        ["ویزای Skilled-Worker", "ویزای تحصیلی"],
        ["ویزای خانواده"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    # ریست کردن حالت و داده‌ها
    user_id = str(update.message.chat_id)
    user_states[user_id] = None
    user_data[user_id] = {}

    await update.message.reply_text(
        "سلام! من ربات خدمات مهاجرت به استرالیا هستم. چطور می‌تونم کمک کنم؟",
        reply_markup=reply_markup
    )

# مدیریت پاسخ‌های کاربر
async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.chat_id)
    user_response = update.message.text

    # مدیریت حالت‌ها
    if user_states.get(user_id) is None:
        if user_response == "ویزای Skilled-Worker":
            user_states[user_id] = "birthdate"
            user_data[user_id] = {"visa_type": "Skilled-Worker"}
            await update.message.reply_text("تاریخ تولد خود را وارد کنید (به‌صورت YYYY-MM-DD):")
        else:
            await update.message.reply_text("فعلاً فقط ویزای Skilled-Worker پشتیبانی می‌شود.")
    elif user_states[user_id] == "birthdate":
        try:
            age = calculate_age(user_response)
            user_data[user_id]["age"] = age
            user_states[user_id] = "education"

            keyboard = [
                ["دیپلم", "کاردانی"],
                ["کارشناسی", "کارشناسی ارشد"],
                ["دکتری"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

            await update.message.reply_text("آخرین مدرک تحصیلی شما چیست؟", reply_markup=reply_markup)
        except ValueError:
            await update.message.reply_text("لطفاً تاریخ تولد را به‌صورت صحیح (YYYY-MM-DD) وارد کنید.")
    elif user_states[user_id] == "education":
        user_data[user_id]["education"] = user_response
        user_states[user_id] = "language"

        keyboard = [
            ["ضعیف (پایینتر از B1)", "متوسط (‌‌B1 و B2)"],
            ["قوی (بالاتر از B2)"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text("سطح زبان خود را انتخاب کنید:", reply_markup=reply_markup)
    elif user_states[user_id] == "language":
        user_data[user_id]["language"] = user_response
        user_states[user_id] = "done"

        # محاسبه امتیاز
        score = calculate_score(user_data[user_id])

        # ذخیره داده‌ها
        save_to_file(user_data)

        # مسیر انتخابی برای کاربر
        keyboard = [
            ["تماس با مشاور", "شروع دوباره"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            f"امتیاز شما محاسبه شد: {score}\nمتشکریم که از خدمات ما استفاده کردید! حالا یکی از گزینه‌های زیر رو انتخاب کنید:",
            reply_markup=reply_markup
        )
    elif user_states[user_id] == "done":
        if user_response == "تماس با مشاور":
            await update.message.reply_text(
                "برای تماس با مشاور، لطفاً به آیدی زیر پیام دهید:\n@PouryaP"
            )
        elif user_response == "شروع دوباره":
            await start(update, context)
        else:
            await update.message.reply_text("لطفاً یکی از گزینه‌های بالا رو انتخاب کنید.")
    else:
        await update.message.reply_text("متوجه نشدم. لطفاً دوباره تلاش کنید.")

# تنظیمات ربات
if __name__ == "__main__":
    app = ApplicationBuilder().token("8099865863:AAHxaeulviM5E5tlpB-cQiol9bymdlj8Cr0").build()

    app.add_handler(CommandHandler("start", start))  # مدیریت دستور /start
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))  # مدیریت پاسخ‌های کاربر

    app.run_polling()
