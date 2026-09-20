from google import genai
from django.conf import settings


def ai_handler(prompt_text):
    api_key = getattr(settings, 'GEMINI_API_KEY', None)

    if not api_key:
        return "Xatolik: GEMINI_API_KEY topilmadi. .env faylingizni tekshiring."

    try:
        # Yangi google-genai mijozi
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt_text,
            config={
                "system_instruction": "Siz professional diyetolog va shaxsiy fitnes trenergiz. Javoblaringizni o'zbek tilida bering."
            }
        )
        return response.text

    except Exception as e:
        return f"Gemini AI bilan bog'lanishda xatolik yuz berdi: {str(e)}"