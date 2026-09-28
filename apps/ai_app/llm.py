import hashlib
import logging
from functools import lru_cache
from django.conf import settings
from django.core.cache import cache
from groq import Groq

logger = logging.getLogger(__name__)

MODEL = "openai/gpt-oss-120b"


@lru_cache(maxsize=1)
def get_client():
    return Groq(api_key=settings.GROQ_API_KEY, timeout=8.0, max_retries=1)


def cached_completion(namespace, payload, messages, ttl=60 * 60 * 24, **kwargs):
    if not getattr(settings, 'GROQ_API_KEY', None):
        return "AI xizmati uchun API kalit sozlanmagan."

    key = f"llm:{namespace}:" + hashlib.sha256(payload.encode()).hexdigest()
    result = cache.get(key)
    if result is not None:
        return result

    try:
        resp = get_client().chat.completions.create(model=MODEL, messages=messages, **kwargs)
        result = resp.choices[0].message.content
        cache.set(key, result, ttl)
        return result
    except Exception:
        logger.exception("Groq API bilan bog'lanishda xatolik yuz berdi")
        return "AI xizmati vaqtincha mavjud emas. Iltimos, keyinroq qayta urinib ko'ring."