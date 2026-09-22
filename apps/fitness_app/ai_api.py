import json
import os
from groq import Groq
from django.conf import settings


def generate_user_advice(self, profile, card_id, period, user_plans):
    buyi = getattr(profile, 'buyi', 'Nomalum')
    vazni = getattr(profile, 'vazni', 'Nomalum')
    maqsadi = getattr(profile, 'maqsadi', 'Nomalum')

    api_key = getattr(settings, 'GROQ_API_KEY', None) or os.getenv("GROQ_API_KEY")

    if not api_key:
        print("Xatolik: GROQ_API_KEY topilmadi.")
        return {
            "nutrition": f"Ratsioningizda oqsilni oshiring va kamida {float(vazni) * 35 / 1000 if str(vazni).replace('.', '', 1).isdigit() else 2}L suv iching.",
            "workout": "Haftasiga 3 marta mashg'ulot bajaring.",
            "ai_recommendation": "Kunlik uyqu va ovqatlanish rejimiga amal qiling."
        }

    prompt = f"""
        Men(AI) professional fitness va ovqatlanish bo'yicha sun'iy intellekt murabbiyisiman.
        Foydalanuvchi ma'lumotlari:
        - Bo'yi: {buyi} cm
        - Vazni: {vazni} kg
        - Maqsadi: {maqsadi}
        - Tanlangan yo'nalish (karta): {card_id}
        - Davriylik: {period}

        Javobni FAQAT quyidagi JSON formatida qaytaring:
        {{
            "nutrition": "Foydalanuvchining bo'yi, vazni va maqsadi uchun aniq kaloriya, oqsil hamda suv miqdori bo'yicha tavsiya",
            "workout": "Ushbu maqsad va davr uchun mos keladigan aniq mashqlar va ularning takrorlanishlar soni",
            "ai_recommendation": "Tiklanish, uyqu va natijaga erishish bo'yicha muhim maslahat"
        }}
    """

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": "Siz professional fitness murabbiyisiz. Javobingiz faqat so'ralgan JSON formatida bo'lishi shart."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
        )

        advice_json = json.loads(response.choices[0].message.content)
        return advice_json

    except Exception as e:
        print("Groq API Xatolik: ", e)

        return {
            "nutrition": f"Ratsioningizda oqsilni oshiring va kamida {float(vazni) * 35 / 1000 if str(vazni).replace('.', '', 1).isdigit() else 2}L suv iching.",
            "workout": "Haftasiga 3 marta mashg'ulot bajaring.",
            "ai_recommendation": "Kunlik uyqu va ovqatlanish rejimiga amal qiling."
        }