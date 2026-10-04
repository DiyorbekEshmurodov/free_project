"""Groq (LLM) bilan ishlashning YAGONA joyi.

Ilgari klient 3 joyda (settings.py, services.py, fitness_app/ai_api.py)
alohida yaratilardi va import paytida API kalit bo'lmasa xato berardi.
Endi: klient kerak bo'lganda yaratiladi (lazy), kesh, kvota va xatolarni
logga yozish shu modulda.
"""
import hashlib
import logging
from datetime import date
from functools import lru_cache

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

MODEL = "openai/gpt-oss-120b"
NO_KEY_MESSAGE = "AI xizmati uchun API kalit sozlanmagan."
UNAVAILABLE_MESSAGE = "AI xizmati vaqtincha mavjud emas. Iltimos, keyinroq qayta urinib ko'ring."
QUOTA_MESSAGE = "Bugungi AI so'rovlar limiti tugadi. Iltimos, ertaga qayta urinib ko'ring."


@lru_cache(maxsize=1)
def get_client():
    from groq import Groq  # lazy import: kalit/kutubxona yo'q bo'lsa ilova qulamaydi
    return Groq(api_key=settings.GROQ_API_KEY, timeout=8.0, max_retries=1)


def _daily_limit() -> int:
    return int(getattr(settings, 'AI_DAILY_LIMIT', 30))


def consume_quota(user_id) -> bool:
    """Foydalanuvchining kunlik AI kvotasidan 1 ta ishlatadi.

    True  - ruxsat bor. False - limit tugagan (model chaqirilmaydi).
    Kvota keshda saqlanadi: ko'p workerli deployda REDIS_URL kerak
    (umumiy kesh bo'lmasa har bir worker alohida sanaydi).
    """
    if user_id is None:
        return True
    key = f"ai_quota:{user_id}:{date.today().isoformat()}"
    cache.add(key, 0, timeout=60 * 60 * 25)
    try:
        used = cache.incr(key)
    except ValueError:  # kalit shu orada o'chib ketgan bo'lsa
        cache.set(key, 1, timeout=60 * 60 * 25)
        used = 1
    return used <= _daily_limit()


def cached_completion(namespace, payload, messages, user_id=None,
                      ttl=60 * 60 * 24, **kwargs):
    """Keshlangan LLM javobi.

    Tartib: kesh -> (faqat kesh bo'lmasa) kvota -> model. Kesh orqali
    kelgan javob uchun xarajat ham, kvota ham sarflanmaydi.
    """
    if not getattr(settings, 'GROQ_API_KEY', None):
        return NO_KEY_MESSAGE

    key = f"llm:{namespace}:" + hashlib.sha256(payload.encode()).hexdigest()
    result = cache.get(key)
    if result is not None:
        return result

    if not consume_quota(user_id):
        return QUOTA_MESSAGE

    try:
        resp = get_client().chat.completions.create(model=MODEL, messages=messages, **kwargs)
        result = resp.choices[0].message.content
        cache.set(key, result, ttl)
        return result
    except Exception:
        logger.exception("Groq API bilan bog'lanishda xatolik yuz berdi")
        return UNAVAILABLE_MESSAGE
