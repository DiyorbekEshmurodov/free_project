import hashlib
from django.core.cache import cache
from django.conf import settings
from groq import Groq

# Yagona Groq klientini yaratish
client = Groq(api_key=getattr(settings, 'GROQ_API_KEY', ''))


def get_cached_llm_completion(prompt: str, timeout: int = 86400) -> str:
    """
    LLM javoblarini keshlaydi (sukunat bo'yicha 24 soat) va 10s taymaut o'rnatadi.
    """
    if not prompt:
        return ""

    # Prompt uchun unikal kesh kaliti (MD5 hash) yaratish
    prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
    cache_key = f"llm_response_{prompt_hash}"

    # 1. Keshdan izlash
    cached_response = cache.get(cache_key)
    if cached_response:
        return cached_response

    try:
        # 2. Taymaut bilan Groq API ga murojaat qilish (max 10 soniya)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
            timeout=10.0
        )
        result = response.choices[0].message.content

        # 3. Natijani keshga saqlash
        cache.set(cache_key, result, timeout)
        return result
    except Exception as e:
        print(f"Groq API xatosi: {e}")
        return "Ayni vaqtda xizmatda uzilish yuz berdi. Iltimos, bir ozdan so'ng qayta urinib ko'ring."