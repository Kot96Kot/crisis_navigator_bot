import json
import os
import datetime
import logging

CACHE_FILE = os.path.abspath("horoscope_cache.json")

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


def get_horoscope(sign_code):
    """Return horoscope text for the given sign from cache only."""
    today = datetime.date.today().isoformat()
    cache = load_cache()
    if cache.get("date") != today:
        logger.error("Horoscope cache for %s is outdated", sign_code)
        return "Сегодня гороскоп не найден, попробуйте позже."
    horoscope = cache.get("horoscopes", {}).get(sign_code)
    if not horoscope:
        logger.error("Horoscope for %s not found in cache", sign_code)
        return "Сегодня гороскоп не найден, попробуйте позже."
    logger.info("Delivering horoscope for %s from cache", sign_code)
    return horoscope
