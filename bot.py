import os
import logging
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

# Load bot token from .env or environment variable
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_TOKEN environment variable not set. Add it to your .env file."
    )

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
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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
    logger.exception("Exception while handling an update")


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()


    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    logger.info("Bot started")
    application.run_polling()


if __name__ == "__main__":
    main()
