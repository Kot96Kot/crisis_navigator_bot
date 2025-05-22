import os
import threading
from flask import Flask
from dotenv import load_dotenv

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает! Добро пожаловать 👋"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters,
    ContextTypes, ConversationHandler
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

WELCOME_TEXT = (
    "🌱 Привет! Ты в «Нейропроводнике» — здесь тебя принимают без осуждения и оценок.\n\n"
    "🧠 Расскажи о тревоге, страхе или тупике — я внимательно вчитаюсь в твои слова и, как психолог и друг, отвечу честно, бережно и с заботой в течение суток.\n\n"
    "🤲 Здесь можно быть собой, без стыда и масок.\n\n"
    "✨ Жми «Начать разбор» — я рядом, чтобы поддержать, даже если мир кажется сложным.\n\n"
    "👋 Как это работает:\n\n"
    "💬 Пиши свой запрос в любое время — я лично читаю каждое сообщение и отвечаю честно, без шаблонов.\n\n"
    "🤖 Я использую современные AI-инструменты, чтобы разбирать ситуацию глубже и найти новые решения.\n\n"
    "🔒 Всё общение строго конфиденциально и остаётся только между нами.\n\n"
    "❗️ Если ситуация критическая — обязательно обратись к врачам или в экстренные службы."
)
SECOND_WELCOME = (
    "💫 Я человек — психолог, и моя задача здесь проста: быть рядом, когда тебе тяжело, и поддержать, как может только настоящий друг. Я много учился не только помогать, но и по-настоящему слушать. В нашем диалоге нет формальностей: я не оцениваю, не спешу советовать, а стараюсь понять и разделить твои чувства.\n\n"
    "Здесь можно говорить откровенно и быть собой. Я рядом, чтобы вместе найти свет даже в самом сложном дне. Не держи всё в себе — ты уже сделал первый шаг, просто написав здесь."
)
FAQ_TEXT = (
    "🌱 Добро пожаловать в «НейроПроводник»!\n\n"
    "Здесь тебя поддержит психолог: можно писать в любое время, а ответ обычно приходит в течение дня.\n\n"
    "Всё по-доброму, анонимно и без осуждения — чтобы ты мог быть собой и не оставался один на один со своими чувствами.\n\n"
    "✨ В «НейроПроводнике» нет шаблонных советов и готовых “лекарств”. Я подхожу к каждому разговору с заботой и вниманием, чтобы вместе находить пути даже там, где кажется тупик. Твоя история здесь важна, а твои чувства — в безопасности.\n"
    "☕️ Иногда хочется не только получить поддержку, но и самому сделать что-то хорошее в ответ. Если у тебя есть желание и возможность — ты можешь поддержать мой труд и развитие «НейроПроводника». Это как угостить меня чашкой кофе, чтобы у меня было больше ресурса оставаться рядом и развивать этот проект: \n"
    "https://www.tbank.ru/cf/e1uIACnwFj \n"
    "Если тебе удобнее — можешь поддержать проект напрямую на карту: 2200-7006-2856-6506 (Т-Банк)\n"
    "Это не обязательно, но любая поддержка — как тёплое “спасибо” и помогает быть рядом для каждого. Главное — не сумма, а твоя благодарность и доверие.\n\n"
    "Всё, что ты чувствуешь, имеет значение. В любой момент — ты можешь обратиться сюда.\n\n"
    "💚 Здесь для тебя всегда открыто место, где можно быть собой.\n"
    "Не держи всё в себе — дай себе шанс выговориться."
)

START_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🚀 Начать разбор", callback_data="go_start")],
    [InlineKeyboardButton("ℹ️ Как это работает?", callback_data="faq")]
])
SECOND_WELCOME_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("Здорово!", callback_data="greeted")]
])
FAQ_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("Да, хочу попробовать", callback_data="go_to_anketa")],
    [InlineKeyboardButton("Позже", callback_data="later")]
])
FINAL_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("📝 Пройти разбор с нуля", callback_data="again")],
    [InlineKeyboardButton("💬 Задать дополнительный вопрос", callback_data="extra")],
    [InlineKeyboardButton("👥 Позвать друга", switch_inline_query="Рекомендую нейро-консультацию: https://t.me/crisis_navigator_bot")],
    [InlineKeyboardButton("ℹ️ FAQ / Как работает", callback_data="faq")],
    [InlineKeyboardButton("🔄 Начать с начала", callback_data="restart")]
])

(NAME, AGE, CHOOSE_EMBODIMENT, EMBODIMENT_Q, EMBODIMENT_R) = range(10, 15)
(Q1, Q2, Q3, Q4, Q5, Q6, REFLECT1, REFLECT2) = range(1, 9)

QUESTIONS = [
    "Привет! Сейчас будут вопросы, которые помогут посмотреть на ситуацию с другой стороны. Некоторые могут быть необычными — отвечай, как чувствуешь. Главное — твои ощущения и мысли.\n\nРасскажи, что сейчас больше всего напрягает или тревожит?\n\n✨ +1 к честности!",
    "Спасибо! Это важно — твои чувства всегда подсказывают, где главный вопрос.\n\nА какая эмоция приходит первой, когда думаешь об этом?\n\n💡 +1 к самопониманию!",
    "Отлично, ты молодец, что делишься! Если представить, что эти эмоции исчезли хотя бы на день, что бы ты захотел(а) сделать первым?\n\n✅ +1 к смелости!",
    "Спасибо! Уже хороший сдвиг. А пробовал(а) раньше что-то менять или делать в похожих ситуациях? Как это сработало для тебя?\n\n🌱 +1 к опыту!",
    "Если хочется — расскажи чуть подробнее, любая мелочь может быть важна.\n\nЕсть ли ощущение маленькой победы сегодня? Что даёт понять, что есть движение?\n\n🚀 +1 к движению!",
    "Если хочешь что-то добавить, уточнить или поделиться деталями — пиши! Всё важно.\n\n🙌 +1 к открытому диалогу!"
]
REFLECTION_1 = "Как тебе сейчас после этих вопросов? Стало ли хоть чуть понятнее или легче?\n\n🪞 +1 к осознанности!"
REFLECTION_2 = "Может, появилось новое ощущение или мысль, которой раньше не было?\n\n🎯 +1 к инсайту!"
EMBODIMENTS = {
  "soul_talk": {
        "title": "🟢 Поговорить по душам",
        "questions": [
            "Что у тебя сегодня на душе? О чём первым захотелось рассказать?",
            "Какая эмоция больше всего звучит внутри прямо сейчас?",
            "Был ли момент, когда стало чуть легче или радостнее?",
            "Что сегодня особенно давит или грузит?",
            "Как ты обычно справляешься с такими днями?",
            "Что бы ты сказал(а) себе, если бы был(а) своим лучшим другом?",
        ],
        "reflections": [
            "После этого разговора что внутри? Появилось ли ощущение поддержки или ясности?",
            "О чём хочется подумать или сделать шаг дальше?"
        ],
        "final": "Ты красавчик! В любой день заслуживаешь поддержки."
    },
    "day_review": {
        "title": "🟠 Быстрый разбор дня",
        "questions": [
            "Какой момент сегодня был самым сложным?",
            "А какой — наоборот, порадовал или дал выдохнуть?",
            "Что именно помогло справиться с трудностями?",
            "О чём тревожишься или переживаешь сейчас?",
            "Что бы изменил(а), если бы мог(ла) вернуться к утру?",
            "Что из сегодняшнего дня хочется взять с собой в завтрашний?",
        ],
        "reflections": [
            "Какая мысль или чувство появились после такого разбора?",
            "О чём хочется поблагодарить себя сегодня?"
        ],
        "final": "Ты красавчик! Каждый день — твой опыт."
    },
    "vent": {
        "title": "🟣 Выпустить пар",
        "questions": [
            "Давай честно: что сегодня выбесило сильнее всего?",
            "Если бы можно было всё высказать без стеснения — что бы сказал(а)?",
            "Как обычно справляешься с такими эмоциями?",
            "Кому бы ты сейчас кинул(а) камень… или комплимент?",
            "Был ли повод для смеха или облегчения сегодня?",
            "Что помогает выдыхать в самые злые дни?",
        ],
        "reflections": [
            "Стало ли легче после “разгрузки”?",
            "Что бы хотел(а) себе пожелать на завтра?"
        ],
        "final": "Ты красавчик! Даже если весь день был “на грани”."
    },
    "resource": {
        "title": "🔵 Поймать ресурс",
        "questions": [
            "Был ли сегодня момент, когда почувствовал(а) себя живым, а не “на автопилоте”?",
            "Что наполнило энергией или хотя бы чуть подняло настроение?",
            "Чем можешь порадовать себя прямо сейчас, пусть даже мелочью?",
            "Кто или что дал сегодня поддержку?",
            "На чём сегодня хочется поставить акцент — на победах или просто на том, что выжил(а)?",
            "Какой ресурс хочется унести с собой в завтрашний день?",
        ],
        "reflections": [
            "Как ты заботишься о себе в трудные моменты?",
            "Какие слова поддержат тебя больше всего?"
        ],
        "final": "Ты красавчик! Всё, что нашёл сегодня — твоя сила."
    },
    "just_talk": {
        "title": "🟤 Просто выговориться",
        "questions": [
            "О чём больше всего хотелось молчать, но всё равно тянет рассказать?",
            "Что внутри хочется выплеснуть — радость, боль, страх или просто усталость?",
            "Если бы тебе гарантировали полное принятие — что бы сказал(а)?",
            "Что сейчас кажется неразрешимым?",
            "Было ли что-то, что сегодня порадовало или вызвало улыбку?",
            "На какую поддержку надеешься (или уже получил(а))?",
        ],
        "reflections": [
            "После этого разговора что отпустило, а что осталось?",
            "Какое слово опишет твоё состояние прямо сейчас?"
        ],
        "final": "Ты красавчик! Главное — не держать в себе."
    },
    "secret_friend": {
        "title": "🕵️‍♂️ Секретный друг",
        "questions": [
            "Что бы ты сейчас рассказал(а) только самому близкому?",
            "Какое чувство труднее всего прятать в себе?",
            "Была ли за сегодня хоть маленькая радость?",
            "Есть ли кто-то, кого не хватает рядом сейчас?",
            "Как обычно справляешься, когда не с кем поделиться?",
            "Что хочется услышать от друга, если честно?",
        ],
        "reflections": [
            "Как тебе после такого разговора?",
            "Стало ли внутри хоть немного спокойнее?"
        ],
        "final": "Спасибо, что доверился — здесь твои слова всегда в безопасности."
    },
    "heart_voice": {
        "title": "❤️ Голос сердца",
        "questions": [
            "О чём твое сердце молчит, но хотелось бы сказать вслух?",
            "Какая эмоция сейчас громче всего звучит внутри?",
            "Когда в последний раз ты радовался просто так?",
            "Что больше всего греет душу в тяжёлые дни?",
            "Как ты проявляешь заботу о себе?",
            "О чём сейчас мечтается, пусть даже чуть-чуть?",
        ],
        "reflections": [
            "Слушая себя, что понял(а) нового?",
            "Хочется ли поддержать себя чем-то прямо сейчас?"
        ],
        "final": "Ты услышан — и пусть твой внутренний голос всегда будет тебе другом."
    },
    "open_soul": {
        "title": "🤲 Открытая душа",
        "questions": [
            "О чём бы ты рассказал(а), если бы не боялся(ась осуждения?",
            "Что сейчас ранит больше всего?",
            "Были ли моменты сегодня, когда стало легче?",
            "Что бы хотел(а) сказать самому себе, но никак не решался(ась)?",
            "Как ты чувствуешь свою силу внутри, даже если пока не видишь?",
            "Если бы мог(ла) попросить вселенную о чём-то, что бы это было?",
        ],
        "reflections": [
            "После такой откровенности, что изменилось внутри?",
            "О чём хочется поблагодарить себя?"
        ],
        "final": "Здесь всегда можно быть настоящим — без масок, без страха."
    },
    "support_chat": {
        "title": "💬 Чат поддержки",
        "questions": [
            "В чём сейчас особенно нужна поддержка?",
            "Кто был рядом или помогал тебе сегодня?",
            "Как ты обычно себя подбадриваешь?",
            "Когда последний раз тебе говорили тёплые слова?",
            "Что хочешь услышать для поддержки прямо сейчас?",
            "Кому бы сам(а) с удовольствием помог(ла)?",
        ],
        "reflections": [
            "Что почувствовал(а), когда смог(ла) выговориться?",
            "Ощущаешь ли сейчас больше уверенности в себе?"
        ],
        "final": "Здесь тебя всегда поддержат — даже если в остальном мире кажется, что никого нет."
    },
    "quiet_harbor": {
        "title": "🌊 Тихая гавань",
        "questions": [
            "Где твоя “тихая гавань” — мысленно или наяву?",
            "Что обычно помогает тебе восстановиться после трудного дня?",
            "Какая мелочь сегодня принесла покой или улыбку?",
            "Когда тебе удавалось почувствовать спокойствие последний раз?",
            "О чём хочется забыть хотя бы на время?",
            "Чем бы наполнил(а) своё тихое место — звуками, запахами, мыслями?",
        ],
        "reflections": [
            "Чувствуешь ли ты сейчас чуть больше спокойствия?",
            "Как хочешь заботиться о себе в ближайшие дни?"
        ],
        "final": "Твоя гавань всегда открыта — возвращайся сюда, когда захочешь тишины и принятия."
    }
}
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.message:
        await update.message.reply_text(WELCOME_TEXT, reply_markup=START_KEYBOARD)
    elif update.callback_query:
        await update.callback_query.message.reply_text(WELCOME_TEXT, reply_markup=START_KEYBOARD)

async def on_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    if data == "go_start":
        await query.edit_message_text(
            SECOND_WELCOME,
            reply_markup=SECOND_WELCOME_KEYBOARD
        )
    elif data == "greeted":
        await query.edit_message_text("Давай познакомимся! Как мне к тебе обращаться? (Имя)")
        return NAME
    elif data == "faq":
        await query.edit_message_text(
            FAQ_TEXT,
            reply_markup=FAQ_KEYBOARD,
        )
    elif data == "go_to_anketa":
        await query.edit_message_text("Отлично! Как мне к тебе обращаться? (Имя)")
        return NAME
    elif data == "later":
        await query.edit_message_text("Если захочешь вернуться — просто напиши /start или выбери из меню.")
    elif data == "extra":
        await query.edit_message_text("Напиши свой дополнительный вопрос, и я передам его эксперту лично.")
        context.user_data['wait_extra'] = True
    elif data == "again":
        await query.edit_message_text("Давай начнём новый разбор!\nКак мне к тебе обращаться? (Имя)")
        return NAME
    elif data == "restart":
        await query.message.reply_text(WELCOME_TEXT, reply_markup=START_KEYBOARD)

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("Сколько тебе лет? (Укажи просто число)")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or not (0 < int(text) < 120):
        await update.message.reply_text("Пожалуйста, напиши возраст цифрами (от 1 до 120).")
        return AGE
    context.user_data["age"] = text

    # --- Кнопки: ВСЕ сценарии + "Не знаю" ---
    embodiment_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(e["title"], callback_data=f"embody_{key}")]
        for key, e in EMBODIMENTS.items()
    ] + [
        [InlineKeyboardButton("🤔 Не знаю — просто классический разбор", callback_data="classic_review")]
    ])
    await update.message.reply_text(
        "Что тебе по душе? Выбери свой сценарий 👇",
        reply_markup=embodiment_keyboard
    )
    return CHOOSE_EMBODIMENT

async def on_embodiment_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "classic_review":
        await query.edit_message_text("Начнём классический разбор!\n\n" + QUESTIONS[0])
        context.user_data["current_q"] = 0
        return Q1

    chosen_key = data.replace("embody_", "")
    context.user_data["embodiment"] = chosen_key
    questions = EMBODIMENTS[chosen_key]["questions"]
    context.user_data["questions"] = questions
    context.user_data["reflections"] = EMBODIMENTS[chosen_key]["reflections"]
    context.user_data["final"] = EMBODIMENTS[chosen_key]["final"]
    await query.edit_message_text(f"Ты выбрал: {EMBODIMENTS[chosen_key]['title']}\n\nДавай начнем!")
    await query.message.reply_text(questions[0])
    context.user_data["current_q"] = 0
    return EMBODIMENT_Q

# Классические вопросы:
async def q1(update, context): context.user_data['q1'] = update.message.text.strip(); await update.message.reply_text(QUESTIONS[1]); return Q2
async def q2(update, context): context.user_data['q2'] = update.message.text.strip(); await update.message.reply_text(QUESTIONS[2]); return Q3
async def q3(update, context): context.user_data['q3'] = update.message.text.strip(); await update.message.reply_text(QUESTIONS[3]); return Q4
async def q4(update, context): context.user_data['q4'] = update.message.text.strip(); await update.message.reply_text(QUESTIONS[4]); return Q5
async def q5(update, context): context.user_data['q5'] = update.message.text.strip(); await update.message.reply_text(QUESTIONS[5]); return Q6
async def q6(update, context): context.user_data['q6'] = update.message.text.strip(); await update.message.reply_text(REFLECTION_1); return REFLECT1
async def reflect1(update, context): context.user_data['reflect1'] = update.message.text.strip(); await update.message.reply_text(REFLECTION_2); return REFLECT2

async def reflect2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reflect2'] = update.message.text.strip()
    name = context.user_data.get('name', '—')
    age = context.user_data.get('age', '—')
    summary = f"""🧑‍💼 Новый клиент:\nИмя: {name}\nВозраст: {age}\n\n🔎 Карта разбора:\n1. {QUESTIONS[0].splitlines()[-3]} — {context.user_data['q1']}\n2. {QUESTIONS[1].splitlines()[-3]} — {context.user_data['q2']}\n3. {QUESTIONS[2].splitlines()[-3]} — {context.user_data['q3']}\n4. {QUESTIONS[3].splitlines()[-3]} — {context.user_data['q4']}\n5. {QUESTIONS[4].splitlines()[-3]} — {context.user_data['q5']}\n6. {QUESTIONS[5].splitlines()[-3]} — {context.user_data['q6']}\n\n🪞 Саморефлексия:\n{REFLECTION_1.splitlines()[0]} — {context.user_data['reflect1']}\n{REFLECTION_2.splitlines()[0]} — {context.user_data['reflect2']}\n"""
    user_chat_id = update.message.chat_id
    try:
        if ADMIN_ID:
            await context.bot.send_message(ADMIN_ID, summary)
            await context.bot.send_message(
                ADMIN_ID,
                f"ID клиента для ответа: /reply <code>{user_chat_id}</code>",
                parse_mode="HTML"
            )
    except Exception as e:
        print("Ошибка при отправке админу:", e)
    await update.message.reply_text(
        "Спасибо, твои ответы уже у эксперта.\n\n "
        "💬 Я внимательно всё прочитаю и подготовлю для тебя персональный разбор — обычно это занимает до суток, ведь хочется по-настоящему вникнуть в твой запрос.\n\n"
        "Не переживай, ты на связи — и как только разбор будет готов, ты сразу его получишь. А пока можешь посмотреть дополнительные возможности ниже 👇 Ответ скоро будет, держу связь! 🙌\n\n",
        reply_markup=FINAL_KEYBOARD
    )
    return ConversationHandler.END

# Вот обновлённые сценарные обработчики (универсальные):
async def embodiment_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_num = context.user_data["current_q"] + 1
    questions = context.user_data["questions"]
    answers = context.user_data.setdefault("embodiment_answers", [])

    user = update.message.from_user
    answer_text = ""

    if update.message.text:
        answer_text = update.message.text.strip()
    elif update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        answer_text = "[Фото отправлено]"
        if ADMIN_ID:
            await context.bot.send_photo(
                ADMIN_ID, photo=photo_file_id,
                caption=f"Фото от @{user.username or user.first_name} (id: {user.id})\nК вопросу: {questions[context.user_data['current_q']]}"
            )
    elif update.message.voice:
        answer_text = "[Голосовое сообщение отправлено]"
        if ADMIN_ID:
            await context.bot.send_voice(
                ADMIN_ID, voice=update.message.voice.file_id,
                caption=f"Голосовое от @{user.username or user.first_name} (id: {user.id})\nК вопросу: {questions[context.user_data['current_q']]}"
            )
    elif update.message.audio:
        answer_text = "[Аудио отправлено]"
        if ADMIN_ID:
            await context.bot.send_audio(
                ADMIN_ID, audio=update.message.audio.file_id,
                caption=f"Аудио от @{user.username or user.first_name} (id: {user.id})\nК вопросу: {questions[context.user_data['current_q']]}"
            )
    elif update.message.document:
        answer_text = "[Документ отправлен]"
        if ADMIN_ID:
            await context.bot.send_document(
                ADMIN_ID, document=update.message.document.file_id,
                caption=f"Документ от @{user.username or user.first_name} (id: {user.id})\nК вопросу: {questions[context.user_data['current_q']]}"
            )
    elif update.message.video:
        answer_text = "[Видео отправлено]"
        if ADMIN_ID:
            await context.bot.send_video(
                ADMIN_ID, video=update.message.video.file_id,
                caption=f"Видео от @{user.username or user.first_name} (id: {user.id})\nК вопросу: {questions[context.user_data['current_q']]}"
            )
    else:
        answer_text = "[Неизвестный тип файла]"

    answers.append(answer_text)

    if q_num < len(questions):
        context.user_data["current_q"] = q_num
        await update.message.reply_text(questions[q_num])
        return EMBODIMENT_Q
    else:
        await update.message.reply_text(context.user_data["reflections"][0])
        context.user_data["current_r"] = 0
        return EMBODIMENT_R

async def embodiment_reflections(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r_num = context.user_data["current_r"] + 1
    reflections = context.user_data["reflections"]
    answers = context.user_data.setdefault("embodiment_reflect", [])
    user = update.message.from_user
    answer_text = ""

    if update.message.text:
        answer_text = update.message.text.strip()
    elif update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        answer_text = "[Фото отправлено]"
        if ADMIN_ID:
            await context.bot.send_photo(
                ADMIN_ID, photo=photo_file_id,
                caption=f"Фото (рефлексия) от @{user.username or user.first_name} (id: {user.id})"
            )
    elif update.message.voice:
        answer_text = "[Голосовое сообщение отправлено]"
        if ADMIN_ID:
            await context.bot.send_voice(
                ADMIN_ID, voice=update.message.voice.file_id,
                caption=f"Голосовое (рефлексия) от @{user.username or user.first_name} (id: {user.id})"
            )
    elif update.message.audio:
        answer_text = "[Аудио отправлено]"
        if ADMIN_ID:
            await context.bot.send_audio(
                ADMIN_ID, audio=update.message.audio.file_id,
                caption=f"Аудио (рефлексия) от @{user.username or user.first_name} (id: {user.id})"
            )
    elif update.message.document:
        answer_text = "[Документ отправлен]"
        if ADMIN_ID:
            await context.bot.send_document(
                ADMIN_ID, document=update.message.document.file_id,
                caption=f"Документ (рефлексия) от @{user.username or user.first_name} (id: {user.id})"
            )
    elif update.message.video:
        answer_text = "[Видео отправлено]"
        if ADMIN_ID:
            await context.bot.send_video(
                ADMIN_ID, video=update.message.video.file_id,
                caption=f"Видео (рефлексия) от @{user.username or user.first_name} (id: {user.id})"
            )
    else:
        answer_text = "[Неизвестный тип файла]"

    answers.append(answer_text)

    if r_num < len(reflections):
        context.user_data["current_r"] = r_num
        await update.message.reply_text(reflections[r_num])
        return EMBODIMENT_R
    else:
        name = context.user_data.get("name", "—")
        age = context.user_data.get("age", "—")
        embodiment_key = context.user_data.get("embodiment", "—")
        embodiment_title = EMBODIMENTS[embodiment_key]["title"] if embodiment_key in EMBODIMENTS else "—"
        questions = context.user_data.get("questions", [])
        answers = context.user_data.get("embodiment_answers", [])
        reflections = context.user_data.get("reflections", [])
        reflect_answers = context.user_data.get("embodiment_reflect", [])

        summary = (
            f"🧑‍💼 Новый клиент:\n"
            f"Имя: {name}\n"
            f"Возраст: {age}\n"
            f"Сценарий: {embodiment_title}\n\n"
            "🔎 Карта разбора:\n"
        )
        for idx, q in enumerate(questions):
            summary += f"{idx+1}. {q} — {answers[idx] if idx < len(answers) else '-'}\n"
        summary += "\n🪞 Саморефлексия:\n"
        for idx, r in enumerate(reflections):
            summary += f"{r} — {reflect_answers[idx] if idx < len(reflect_answers) else '-'}\n"

        user_chat_id = update.message.chat_id
        try:
            if ADMIN_ID:
                await context.bot.send_message(ADMIN_ID, summary)
                await context.bot.send_message(
                    ADMIN_ID,
                    f"ID клиента для ответа: /reply <code>{user_chat_id}</code>",
                    parse_mode="HTML"
                )
        except Exception as e:
            print("Ошибка при отправке админу:", e)

        await update.message.reply_text(
            "Спасибо, твои ответы уже у эксперта.\n\n"
            "💬 Я внимательно всё прочитаю и подготовлю для тебя персональный разбор — обычно это занимает до суток, ведь хочется по-настоящему вникнуть в твой запрос.\n\n"
            "Не переживай, ты на связи — и как только разбор будет готов, ты сразу его получишь. А пока можешь посмотреть дополнительные возможности ниже 👇 Ответ скоро будет, держу связь! 🙌\n\n",
            reply_markup=FINAL_KEYBOARD
        )
        return ConversationHandler.END

async def forward_extra_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    if context.user_data.get('wait_extra'):
        if ADMIN_ID:
            await context.bot.send_message(
                ADMIN_ID,
                f"📩 Новый дополнительный вопрос/комментарий от @{user.username or user.first_name} (id: {user.id}):\n\n{text}"
            )
        await update.message.reply_text(
            "Спасибо, твой вопрос отправлен! Психолог скоро ответит лично сюда."
        )
        context.user_data['wait_extra'] = False

async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Нет доступа.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Формат: /reply <chat_id> <текст>")
        return

    chat_id = context.args[0]
    text = " ".join(context.args[1:])

    try:
        await context.bot.send_message(chat_id=int(chat_id), text=text)
        await update.message.reply_text("Ответ отправлен ✅")
    except Exception as e:
        await update.message.reply_text(f"Ошибка отправки: {e}")

async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Начать с нуля"),
        BotCommand("cancel", "Отменить диалог"),
        BotCommand("reply", "Ответить клиенту (для админа)")
    ])

def main():
    app_tg = ApplicationBuilder().token(BOT_TOKEN).post_init(set_commands).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(on_callback_query)
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            CHOOSE_EMBODIMENT: [CallbackQueryHandler(on_embodiment_chosen, pattern="^(embody_|classic_review)")],
            EMBODIMENT_Q: [MessageHandler(filters.ALL & ~filters.COMMAND, embodiment_questions)],
            EMBODIMENT_R: [MessageHandler(filters.ALL & ~filters.COMMAND, embodiment_reflections)],
            Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, q1)],
            Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, q2)],
            Q3: [MessageHandler(filters.TEXT & ~filters.COMMAND, q3)],
            Q4: [MessageHandler(filters.TEXT & ~filters.COMMAND, q4)],
            Q5: [MessageHandler(filters.TEXT & ~filters.COMMAND, q5)],
            Q6: [MessageHandler(filters.TEXT & ~filters.COMMAND, q6)],
            REFLECT1: [MessageHandler(filters.TEXT & ~filters.COMMAND, reflect1)],
            REFLECT2: [MessageHandler(filters.TEXT & ~filters.COMMAND, reflect2)],
        },
        fallbacks=[CommandHandler("cancel", start)],
        per_message=False,
        per_chat=True,
    )

    app_tg.add_handler(conv_handler)
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_extra_message))
    app_tg.add_handler(CommandHandler("reply", reply_command))

    print("Бот запущен!")
    app_tg.run_polling()

if __name__ == "__main__":
    load_dotenv()
    threading.Thread(target=run_flask, daemon=True).start()
    main()
