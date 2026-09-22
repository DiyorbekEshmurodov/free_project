from groq import Groq
from django.conf import settings


def ai_handler(prompt_text):
    api_key = getattr(settings, 'GROQ_API_KEY', None)

    if not api_key:
        return "Xatolik: GROQ_API_KEY topilmadi. .env faylingizni tekshiring."

    try:
        # Groq clientini yaratamiz
        client = Groq(api_key=api_key)

        # Groq API ga so'rov yuboramiz
        response = client.chat.completions.create(
            # Groq'da tavsiya etilgan eng kuchli va tezkor modellardan biri (Llama 3.3 70B):
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Siz professional diyetolog va shaxsiy fitnes trenergiz. Javoblaringizni o'zbek tilida bering."
                },
                {
                    "role": "user",
                    "content": prompt_text
                }
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Groq AI bilan bog'lanishda xatolik yuz berdi: {str(e)}"