import json
import logging

from django.conf import settings

from apps.ai_app.llm import cached_completion

logger = logging.getLogger(__name__)

PERIOD_LABELS = {'daily': 'kunlik', 'weekly': 'haftalik', 'monthly': 'oylik', 'yearly': 'yillik'}
ADVICE_KEYS = ('nutrition', 'workout', 'ai_recommendation', 'timeline')
DISCLAIMER = "Bu umumiy ma'lumot; natija odamga qarab farq qiladi. Sog'liq bilan bog'liq savollar bo'lsa, shifokor bilan maslahatlashing."

FALLBACK_TEXTS = {
    'weight_loss': {
        'nutrition': "Sabzavot, oqsilli mahsulotlar va yetarli suvni ratsioningizga kiriting; shakarli ichimliklar va ortiqcha shirinliklarni kamaytirishga harakat qiling.",
        'workout': "Haftasiga bir necha marta yengil kardio (yurish, yugurish) va umumiy kuch mashqlarini bosqichma-bosqich boshlang.",
        'ai_recommendation': "Barqaror uyqu va tartibli ovqatlanish metabolizm uchun muhim. Keskin cheklovlardan saqlaning.",
        'timeline': "Natija sur'ati odamga qarab farq qiladi; sekin va barqaror o'zgarish odatda uzoq muddatda yaxshiroq saqlanadi.",
    },
    'muscle_gain': {
        'nutrition': "Har bir taomda yetarli oqsil (go'sht, baliq, tuxum, dukkaklilar) va umumiy kaloriyani ehtiyojingizga moslab oshirishni ko'rib chiqing.",
        'workout': "Bazaviy kuch mashqlarini texnikaga e'tibor berib, o'zingizga mos og'irlikda bajaring; mashq orasida yetarli dam oling.",
        'ai_recommendation': "Mushaklar tiklanishi uchun yetarli uyqu va mashqlar orasida dam kunlari kerak.",
        'timeline': "Mushak o'sishi sekin kechadi va individual; muntazamlik natijadan muhimroq ko'rsatkich.",
    },
    'stamina': {
        'nutrition': "Mevalar, ko'katlar, to'liq donli mahsulotlar va yetarli suyuqlik kun davomida energiyani qo'llab-quvvatlashi mumkin.",
        'workout': "Yengil intensivlikdan boshlab yurish yoki yugurish masofasini asta-sekin oshiring; intervalli mashqlarni ehtiyotkorlik bilan kiriting.",
        'ai_recommendation': "Mashq paytida o'zingizni nazorat qiling; bosh aylanishi yoki og'riq bo'lsa to'xtating va shifokorga murojaat qiling.",
        'timeline': "Chidamlilik odatda bir necha hafta muntazam mashqdan keyin sezila boshlaydi, lekin sur'ati har kimda har xil.",
    },
    'health_habits': {
        'nutrition': "Qayta ishlangan taomlarni kamaytirib, ratsionga ko'proq yangi sabzavot va meva qo'shishga harakat qiling.",
        'workout': "Kundalik yurish va ertalabki yengil badan tarbiya kabi kichik odatlardan boshlang.",
        'ai_recommendation': "Har kuni taxminan bir xil vaqtda uxlash va uyg'onish odatlarni mustahkamlashga yordam beradi.",
        'timeline': "Odat shakllanishi vaqt oladi; kichik, bajarish oson qadamlar uzoq muddatda yaxshi ishlaydi.",
    },
}


def _fallback_advice(profile, card_id, period):
    """AI mavjud bo'lmaganda ehtiyotkor, kafolatsiz umumiy matn."""
    p_name = PERIOD_LABELS.get(period, 'haftalik')
    texts = dict(FALLBACK_TEXTS.get(card_id, FALLBACK_TEXTS['health_habits']))
    texts['nutrition'] = f"({p_name.capitalize()} reja) {texts['nutrition']}"
    texts['timeline'] = f"{texts['timeline']} {DISCLAIMER}"
    return texts


def _parse_advice(raw):
    """Model javobini JSON sifatida o'qiydi; noto'g'ri bo'lsa None."""
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(data, dict) or not all(isinstance(data.get(k), str) for k in ADVICE_KEYS):
        return None
    return {k: data[k] for k in ADVICE_KEYS}


def generate_user_advice(profile, card_id, period, *, user_id):
    """Groq orqali maslahat oladi (kesh + kunlik kvota bilan).

    Natija JSON bo'lmasa, kalit yo'q bo'lsa yoki limit tugasa model
    chaqirilmaydi / zaxira matn qaytadi. Zaxira matn hech qanday natijani
    kafolatlamaydi.
    """
    buyi = getattr(profile, 'buyi', None) or 'Nomalum'
    vazni = getattr(profile, 'vazni', None) or 'Nomalum'
    maqsadi = getattr(profile, 'maqsadi', None) or 'Nomalum'

    if not getattr(settings, 'GROQ_API_KEY', None):
        logger.warning("GROQ_API_KEY topilmadi. Zaxira matnga o'tilmoqda.")
        return _fallback_advice(profile, card_id, period)

    prompt = f"""
        Foydalanuvchi ma'lumotlari:
        - Bo'yi: {buyi} cm
        - Vazni: {vazni} kg
        - Maqsadi: {maqsadi}
        - Tanlangan yo'nalish (karta): {card_id}
        - Davriylik: {period}

        Umumiy, ehtiyotkor tavsiya bering. Natijani kafolatlamang, aniq tibbiy tashxis qo'ymang.
        Javobni FAQAT quyidagi JSON formatida qaytaring:
        {{
            "nutrition": "ovqatlanish bo'yicha umumiy tavsiya",
            "workout": "mos mashqlar",
            "ai_recommendation": "tiklanish va uyqu bo'yicha maslahat",
            "timeline": "kutilayotgan jarayon (kafolatsiz)"
        }}
    """
    messages = [
        {"role": "system", "content": "Siz fitness bo'yicha yordamchisiz. Javobingiz faqat so'ralgan JSON formatida bo'lishi shart."},
        {"role": "user", "content": prompt},
    ]

    raw = cached_completion(
        'advice', prompt, messages, user_id=user_id,
        response_format={"type": "json_object"}, temperature=0.5,
    )
    return _parse_advice(raw) or _fallback_advice(profile, card_id, period)
