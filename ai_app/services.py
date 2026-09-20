import google.generativeai as genai
from django.conf import settings

def ai_handler(prompt_text):
    # settings.py orqali .env faylingizdagi GEMINI_API_KEY olinadi
    api_key = getattr(settings, 'GEMINI_API_KEY', None)

    if not api_key:
        return "Xatolik: GEMINI_API_KEY topilmadi. .env faylingizni tekshiring."

    try:
        # Gemini API kalitini sozlash
        genai.configure(api_key=api_key)

        # AI modelini yaratish va tizim ko'rsatmasini (system instruction) berish
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction="Siz professional diyetolog va shaxsiy fitnes trenergiz. Javoblaringizni o'zbek tilida, tushunarli va chiroyli formatda bering."
        )

        # Javobni shakllantirish
        response = model.generate_content(prompt_text)

        return response.text

    except Exception as e:
        return f"Gemini AI bilan bog'lanishda xatolik yuz berdi: {str(e)}"