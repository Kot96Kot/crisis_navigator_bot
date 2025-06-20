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
client = openai.OpenAI(api_key=OPENAI_API_KEY)

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
    """Load horoscope cache from file."""    
    if os.path.exists(CACHE_FILE):
        try:
            logger.info("Loading cache from %s", CACHE_FILE)
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("Failed to load cache")
    return {"date": "", "horoscopes": {}}


def save_cache(data):
    """Save horoscope cache to file."""
    try:
        logger.info("Saving cache to %s", CACHE_FILE)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        logger.exception("Failed to save cache")


PROMPT_TEMPLATE = (
    "Ты — digital-друг, который пишет самый смешной, мемный, но очень тёплый и поддерживающий гороскоп на сегодня для знака {sign}. "
    "Пиши абсолютно без мистики, магии, предсказаний судьбы и ‘удачных дней’. Никаких звёзд, чисел, астрологических клише, шаманских заклинаний и ‘Марса в пятом доме’! "
    "Главное — атмосфера настоящей дружбы, чувство юмора, самоирония и чуткая поддержка. Пиши так, чтобы человек почувствовал: ‘вот это меня знают и реально подбодрили!’\n\n"
    "Структура ответа:\n"
    "1. Начни с эмоционального хука: выбери мемный или бытовой пример, который срезонирует с жизнью знака {sign} сегодня (можешь упомянуть мемы про лень, прокрастинацию, мечты о больших делах, сообщения, которые ‘лежали в голове две недели’ и внезапный прилив вдохновения). \n"
    "2. Сделай остроумный переход к главной мысли дня: чем этот день уникален, что можно увидеть по-новому, что отпустить и где ‘разрешить себе фигню’. \n"
    "3. Дай 2–3 “совета от друга”: это не инструкция, а шуточно-реалистичный разгон, что сегодня можно ‘забить на работу ради 15 минут мемов’, ‘не бояться написать “прости, забыл” старому другу’, ‘выгулять свою прокрастинацию как породистого пса’. \n"
    "4. Добавь мини-историю, как будто сам недавно попал в забавную или странную ситуацию (можно про курьера, который опять привёз чай вместо кофе, или вечную борьбу с будильником, или героический поход в магазин в тапочках).\n"
    "5. Заверши поддержкой — искренней и с юмором: ‘Даже если сегодня все планы рассыпались как печеньки в рюкзаке — ты всё равно на коне, просто этот конь любит отдыхать на диване’.\n\n"
    "Обязательные правила:\n"
    "- Не упоминай магию, планеты, числа, ‘удачу’, ‘энергию’, не предсказывай будущее, не используй астрологические стереотипы.\n"
    "- Можно вставлять отсылки к популярным мемам, сериалам, блогерам, офисной или студенческой жизни, но не делай это единственным содержанием — главное, чтобы всё было к месту.\n"
    "- Используй бытовые сравнения: бытовуха, “рабочая лошадка”, “забытый зум”, “кружка, которую так и не помыл”, “проверка мемов вместо важных дел”.\n"
    "- Каждый раз текст должен быть уникальным, избегай одинаковых фраз и советов.\n"
    "- Не делай коротко — минимум 2-3 абзаца, максимум 6, чтобы реально было что прочитать и улыбнуться.\n"
    "- Отвечай так, будто ты давний друг, который пережил с читателем все его “эпичные” и забавные фейлы.\n"
    "- Пиши просто, понятно, без заумных оборотов, но остроумно и с огоньком.\n\n"
    "Примеры поворотов, которые можно использовать (не цитировать дословно, а брать как идею):\n"
    "- ‘Сегодня день, когда ты наконец-то поймёшь, почему носки всегда теряются только по одному.’\n"
    "- ‘Твои планы на день? Они как кофе в офисе — иногда растворяются ещё до обеда, но настроение можно спасти мемом с котом.’\n"
    "- ‘Если кто-то скажет “действуй!”, действуй… но только после того, как полистаешь мемасы.’\n"
    "- ‘Переписка сегодня заиграет как серенада под балконом, если рискнёшь первым написать. А если нет — будет мем про “зависшие диалоги”.’\n"
    "- ‘Если на пути появится неудача — подари ей стикер и иди дальше. Твой день всё равно будет лучше, чем у того, кто забыл зарядить телефон.’\n\n"
    "В итоге читатель должен почувствовать, что даже если день не идеален, над этим можно посмеяться и двигаться дальше. Мотивация — через юмор, тепло и дружбу.\n"
    "Не повторяйся из раза в раз. Гороскоп должен быть свежим, мемным, ярким и искренним. Не утомляй нравоучениями, не используй скучные шаблоны.\n"
    "Пиши с реальным желанием порадовать и подбодрить — будто бы ты сейчас лично звонишь другу и рассказываешь историю за чашкой чая, а не строчишь текст ради галочки.\n"
)



def generate_all_horoscopes():
    """Generate fresh horoscopes for all signs and save them to cache."""
    logger.info("Starting horoscope generation")
    horoscopes = {}
    for name, code in ZODIAC_SIGNS.items():
        prompt = PROMPT_TEMPLATE.format(sign=name)
        try:
            logger.info("Requesting horoscope for %s", name)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.8,
            )
            text = response.choices[0].message.content.strip()
        except Exception as e:
            logger.exception("Error generating %s: %s", code, e)
            text = "Сегодня гороскоп не найден, попробуйте позже."
        horoscopes[code] = text
    data = {
        "date": datetime.date.today().isoformat(),
        "horoscopes": horoscopes,
    }
    save_cache(data)
    return data

def get_horoscope(sign_code):
    """Return horoscope text for the given sign."""
    today = datetime.date.today().isoformat()
    cache = load_cache()
    if cache.get("date") != today or sign_code not in cache.get("horoscopes", {}):
        logger.info("Cache miss or outdated. Generating new horoscopes")
        cache = generate_all_horoscopes()
    horoscope = cache.get("horoscopes", {}).get(sign_code)
    if not horoscope:
        logger.error("Horoscope for %s not found in cache", sign_code)
        return "Сегодня гороскоп не найден, попробуйте позже."
    logger.info("Delivering horoscope for %s", sign_code)
    return horoscope


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
