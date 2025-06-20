import os
import logging
import asyncio
import datetime
from dotenv import load_dotenv

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from horoscope_utils import ZODIAC_SIGNS, get_horoscope
from text_utils import trim_text
from bot_utils import load_json, save_json

# Load bot token from .env or environment variable
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
if not BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_TOKEN environment variable not set. Add it to your .env file."
    )

STATS_FILE = os.path.abspath("stats.json")
REMINDERS_FILE = os.path.abspath("reminders.json")

# Support legacy button labels with emoji prefixes
EMOJI_TO_NAME = {
    "♈️Овен": "Овен",
    "♉️Телец": "Телец",
    "♊️Близнецы": "Близнецы",
    "♋️Рак": "Рак",
    "♌️Лев": "Лев",
    "♍️Дева": "Дева",
    "♎️Весы": "Весы",
    "♏️Скорпион": "Скорпион",
    "♐️Стрелец": "Стрелец",
    "♑️Козерог": "Козерог",
    "♒️Водолей": "Водолей",
    "♓️Рыбы": "Рыбы",
}


KEYBOARD_LAYOUT = [
    ["♈️Овен", "♉️Телец", "♊️Близнецы"],
    ["♋️Рак", "♌️Лев", "♍️Дева"],
    ["♎️Весы", "♏️Скорпион", "♐️Стрелец"],
    ["♑️Козерог", "♒️Водолей", "♓️Рыбы"],
    ["Назад"],
]
MODE_KEYBOARD = [["Мемный гороскоп", "Нормальный гороскоп"]]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_keyboard():
    return ReplyKeyboardMarkup(KEYBOARD_LAYOUT, resize_keyboard=True)


def get_mode_keyboard():
    return ReplyKeyboardMarkup(MODE_KEYBOARD, resize_keyboard=True)


def get_inline_button():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Карманный психолог | Солнышко, держись ☀️",
                    url="https://t.me/crisis_navigatorbot?start=github_com_kot96kot_crisis_navigator_bot_edit_main_bot_py",
                )
            ]
        ]
    )

def load_stats():
    return load_json(STATS_FILE, {"starts": 0, "signs": {}})


def save_stats(data):
    save_json(STATS_FILE, data)


def increment_start():
    data = load_stats()
    data["starts"] = data.get("starts", 0) + 1
    save_stats(data)


def increment_sign(sign):
    data = load_stats()
    signs = data.setdefault("signs", {})
    signs[sign] = signs.get(sign, 0) + 1
    save_stats(data)


def load_reminders():
    return load_json(REMINDERS_FILE, {"chats": []})


def save_reminders(data):
    save_json(REMINDERS_FILE, data)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    increment_start()
    await update.message.reply_text(
        "Выберите тип гороскопа:", reply_markup=get_mode_keyboard()
    )

async def reminder_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_reminders()
    chat_id = update.effective_chat.id
    if chat_id not in data["chats"]:
        data["chats"].append(chat_id)
        save_reminders(data)
        await update.message.reply_text("Напоминания включены")
    else:
        await update.message.reply_text("Напоминания уже включены")


async def reminder_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_reminders()
    chat_id = update.effective_chat.id
    if chat_id in data["chats"]:
        data["chats"].remove(chat_id)
        save_reminders(data)
        await update.message.reply_text("Напоминания отключены")
    else:
        await update.message.reply_text("Напоминания и так выключены")


async def send_daily_reminders(context: ContextTypes.DEFAULT_TYPE):
    data = load_reminders()
    for chat_id in data.get("chats", []):
        try:
            await context.bot.send_message(
                chat_id=chat_id, text="Проверь сегодня свой гороскоп"
            )
        except Exception:
            logger.exception("Failed to send reminder to %s", chat_id)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    data = load_stats()
    lines = [f"Стартов: {data.get('starts', 0)}"]
    for name, code in ZODIAC_SIGNS.items():
        count = data.get("signs", {}).get(code, 0)
        lines.append(f"{name}: {count}")
    await update.message.reply_text("\n".join(lines))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = update.message.text.strip()
    
    if text == "Назад":
        context.user_data.pop("mode", None)
        await update.message.reply_text(
            "Выберите тип гороскопа:", reply_markup=get_mode_keyboard()
        )
        return

    if text in ("Мемный гороскоп", "Нормальный гороскоп"):
        mode = "meme" if text.startswith("Мем") else "normal"
        context.user_data["mode"] = mode
        await update.message.reply_text(
            "Выберите ваш знак зодиака:", reply_markup=get_keyboard()
        )
        return

    sign_name = EMOJI_TO_NAME.get(text, text)
    sign_code = ZODIAC_SIGNS.get(sign_name)
    if not sign_code:
        await update.message.reply_text(
            "Пожалуйста, выберите знак зодиака из списка.", reply_markup=get_keyboard()
        )
        return
    mode = context.user_data.get("mode", "meme")
    horoscope = get_horoscope(sign_code, mode)
    horoscope = trim_text(horoscope)
    await update.message.reply_text(horoscope)
    increment_sign(sign_code)

    async def delayed_button(chat_id: int):
        await asyncio.sleep(60)
        await context.bot.send_message(
            chat_id=chat_id,
            text="Карманный психолог | Солнышко, держись ☀️",
            reply_markup=get_inline_button(),
        )

    context.application.create_task(delayed_button(update.effective_chat.id))
    await update.message.reply_text(
        "Выберите ваш знак зодиака:", reply_markup=get_keyboard()
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Exception while handling an update")


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()


    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reminder_on", reminder_on))
    application.add_handler(CommandHandler("reminder_off", reminder_off))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    application.job_queue.run_daily(
        send_daily_reminders, time=datetime.time(hour=9, minute=0)
    )


    logger.info("Bot started")
    application.run_polling()


if __name__ == "__main__":
    main()
