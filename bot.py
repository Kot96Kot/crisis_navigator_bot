import json
import os
import logging
import datetime
from dotenv import load_dotenv

import requests
from bs4 import BeautifulSoup
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

# Load bot token from .env or environment variable
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_TOKEN environment variable not set. Add it to your .env file."
    )

CACHE_FILE = "horoscope_cache.json"

ZODIAC_SIGNS = {
    "Овен": "aries",
    "Телец": "taurus",
    "Близнецы": "gemini",
    "Рак": "cancer",
    "Лев": "leo",
    "Дева": "virgo",
    "Весы": "libra",
    "Скорпион": "scorpio",
    "Стрелец": "sagittarius",
    "Козерог": "capricorn",
    "Водолей": "aquarius",
    "Рыбы": "pisces",
}

KEYBOARD_LAYOUT = [
    ["Овен", "Телец", "Близнецы"],
    ["Рак", "Лев", "Дева"],
    ["Весы", "Скорпион", "Стрелец"],
    ["Козерог", "Водолей", "Рыбы"],
]

HORO_URL_TEMPLATE = "https://horo.mail.ru/prediction/{}/today/"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("Failed to load cache")
    return {"date": "", "horoscopes": {}}


def save_cache(data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        logger.exception("Failed to save cache")


def fetch_all_horoscopes():
    logger.info("Fetching horoscopes from website")
    horoscopes = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    for name, code in ZODIAC_SIGNS.items():
        url = HORO_URL_TEMPLATE.format(code)
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print("=== START HTML ===")
            print(response.text[:2000])
            print("=== END HTML ===")            
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            div = soup.find("div", class_="article__text")
            text = div.get_text(separator="\n", strip=True) if div else "Не удалось получить гороскоп."
            horoscopes[code] = text
        except Exception as e:
            logger.exception("Error fetching %s: %s", code, e)
            horoscopes[code] = "Не удалось получить гороскоп. Попробуйте позже."
    data = {
        "date": datetime.date.today().isoformat(),
        "horoscopes": horoscopes,
    }
    save_cache(data)
    return data

def get_horoscope(sign_code):
    today = datetime.date.today().isoformat()
    cache = load_cache()
    if cache.get("date") != today or sign_code not in cache.get("horoscopes", {}):
        cache = fetch_all_horoscopes()
    return cache.get("horoscopes", {}).get(sign_code, "Нет данных.")


def get_keyboard():
    return ReplyKeyboardMarkup(KEYBOARD_LAYOUT, resize_keyboard=True)


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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Выберите ваш знак зодиака:", reply_markup=get_keyboard()
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = update.message.text.strip()
    sign_code = ZODIAC_SIGNS.get(text)
    if not sign_code:
        await update.message.reply_text(
            "Пожалуйста, выберите знак зодиака из списка.", reply_markup=get_keyboard()
        )
        return
    horoscope = get_horoscope(sign_code)
    await update.message.reply_text(horoscope)
    await update.message.reply_text(
        "Карманный психолог | Солнышко, держись ☀️",
        reply_markup=get_inline_button(),
    )
    await update.message.reply_text(
        "Выберите ваш знак зодиака:", reply_markup=get_keyboard()
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    logger.info("Bot started")
    application.run_polling()


if __name__ == "__main__":
    main()
