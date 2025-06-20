import json
import os
import logging
import datetime
from dotenv import load_dotenv

import openai
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY environment variable not set. Add it to your .env file."
    )
openai.api_key = OPENAI_API_KEY

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
    ["Овен", "Телец", "Близнецы"],
    ["Рак", "Лев", "Дева"],
    ["Весы", "Скорпион", "Стрелец"],
    ["Козерог", "Водолей", "Рыбы"],
]

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


PROMPT_TEMPLATE = (
    "Составь смешной, мемный, но при этом по-дружески поддерживающий "
    "гороскоп на сегодня для знака {sign}. "
    "Напиши 2–3 абзаца (примерно 400–600 знаков). "
    "Не делай мистики, не пиши про магию, числа или удачные дни, не используй шаблоны. "
    "Добавь легкий юмор, самоиронию, подбадривай. "
    "Можешь вставить мемный поворот (\u201cНаконец-то дойдут руки до того самого приглашения…\u201d, "
    "\u201cПереписка заиграет как серенада под балконом…\u201d). "
    "Пиши так, будто это совет от старого доброго друга, который знает тебя 100 лет. "
    "Можно использовать сравнения из повседневной жизни, но не делай слишком коротко. Не повторяйся."
)


def generate_all_horoscopes():
    logger.info("Generating horoscopes using OpenAI")
    horoscopes = {}
    for name, code in ZODIAC_SIGNS.items():
        prompt = PROMPT_TEMPLATE.format(sign=name)
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.8,
            )
            text = response.choices[0].message.content.strip()
        except Exception as e:
            logger.exception("Error generating %s: %s", code, e)
            text = "Не удалось получить гороскоп. Попробуйте позже."
        horoscopes[code] = text
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
        cache = generate_all_horoscopes()
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
    sign_name = EMOJI_TO_NAME.get(text, text)
    sign_code = ZODIAC_SIGNS.get(sign_name)
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
