import json
import os
# from google import genai
# from google.genai import types
from openai import OpenAI
from django.conf import settings


def generate_user_advice(self, profile, card_id, period, user_plans):
    buyi = getattr(profile, 'buyi', 'Nomalum')
    vazni = getattr(profile, 'vazni', 'Nomalum')
    maqsadi = getattr(profile, 'maqsadi', 'Nomalum')

    # API kalitni settings.py yoki .env fayldan olish
    api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("Xatolik: GEMINI_API_KEY topilmadi.")
        return {
            "nutrition": f"Ratsioningizda oqsilni oshiring va kamida {float(vazni) * 35 / 1000 if str(vazni).replace('.', '', 1).isdigit() else 2}L suv iching.",
            "workout": "Haftasiga 3 marta mashg'ulot bajaring.",
            "ai_recommendation": "Kunlik uyqu va ovqatlanish rejimiga amal qiling."
        }

    prompt = f"""
        Siz professional fitness va ovqatlanish bo'yicha sun'iy intellekt murabbiyisiz.
        Foydalanuvchi ma'lumotlari:
        - Bo'yi: {buyi} cm
        - Vazni: {vazni} kg
        - Maqsadi: {maqsadi}
        - Tanlangan yo'nalish (karta): {card_id}
        - Davriylik: {period}

        Quyidagi JSON formatida FAQAT va FAQAT toza JSON javob qaytaring (hech qanday ortiqcha markdown va matnsiz):
        {{
            "nutrition": "Foydalanuvchining bo'yi, vazni va maqsadi uchun aniq kaloriya, oqsil hamda suv miqdori bo'yicha tavsiya",
            "workout": "Ushbu maqsad va davr uchun mos keladigan aniq mashqlar va ularning takrorlanishlar soni",
            "ai_recommendation": "Tiklanish, uyqu va natijaga erishish bo'yicha muhim maslahat"
        }}
    """

    try:
        # client = genai.Client(api_key=api_key)
        #
        # response = client.models.generate_content(
        #     model="gemini-3.6-flash",
        #     contents=prompt,
        #     config=types.GenerateContentConfig(
        #         response_mime_type="application/json",
        #         temperature=0.5,
        #     ),
        # )
        #
        # advice_json = json.loads(response.text)
        # return advice_json
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key="SIZNING_OPENROUTER_API_KEYINGIZ",
        )

        response = client.chat.completions.create(
            # Bepul model nomi:
            model="meta-llama/llama-3.3-70b-instruct:free",
            messages=[
                {"role": "system", "content": "Siz foydali yordamchisiz."},
                {"role": "user", "content": "Salom, OpenRouter haqida qisqacha aytib ber."}
            ]
        )

        print(response.choices[0].message.content)



    except Exception as e:
        print("Gemini API Xatolik: ", e)

        return {
            "nutrition": f"Ratsioningizda oqsilni oshiring va kamida {float(vazni) * 35 / 1000 if str(vazni).replace('.', '', 1).isdigit() else 2}L suv iching.",
            "workout": "Haftasiga 3 marta mashg'ulot bajaring.",
            "ai_recommendation": "Kunlik uyqu va ovqatlanish rejimiga amal qiling."
        }