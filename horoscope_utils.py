import json
import os
import datetime
import logging

CACHE_FILES = {
    "meme": os.path.abspath("horoscope_cache_meme.json"),
    "normal": os.path.abspath("horoscope_cache_normal.json"),
}

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


def load_cache(mode: str = "meme"):
    """Load horoscope cache for the given mode from file."""
    path = CACHE_FILES.get(mode, CACHE_FILES["meme"])
    if os.path.exists(path):
        try:
            logger.info("Loading cache from %s", path)
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("Failed to load cache %s", path)
    return {"date": "", "horoscopes": {}}


def save_cache(data, mode: str = "meme"):
    """Save horoscope cache for the given mode to file."""
    path = CACHE_FILES.get(mode, CACHE_FILES["meme"])
    try:
        logger.info("Saving cache to %s", path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        logger.exception("Failed to save cache %s", path)


def get_horoscope(sign_code, mode: str = "meme"):
    """Return horoscope text for the given sign from cache only."""
    today = datetime.date.today().isoformat()
    cache = load_cache(mode)
    if cache.get("date") != today:
        logger.error("Horoscope cache for %s is outdated", sign_code)
        return "Сегодня гороскоп не найден, попробуйте позже."
    horoscope = cache.get("horoscopes", {}).get(sign_code)
    if not horoscope:
        logger.error("Horoscope for %s not found in cache", sign_code)
        return "Сегодня гороскоп не найден, попробуйте позже."
    logger.info("Delivering horoscope for %s from cache", sign_code)
    return horoscope
