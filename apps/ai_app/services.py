from openai import OpenAI
from django.conf import settings


def ai_handler(prompt_text):
    # settings.py faylidan API kalitni olamiz
    api_key = getattr(settings, 'OPENROUTER_API_KEY', None)

    if not api_key:
        return "Xatolik: OPENROUTER_API_KEY topilmadi. .env faylingizni tekshiring."

    try:
        # OpenRouter OpenAI kutubxonasi bilan mos keladi
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        response = client.chat.completions.create(
            # OpenRouter-dagi butunlay bepul modellar:
            # - google/gemini-2.5-flash:free
            # - meta-llama/llama-3.3-70b-instruct:free
            # - qwen/qwen-2.5-72b-instruct:free
            model="qwen/qwen-2.5-72b-instruct:free",
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
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI bilan bog'lanishda xatolik yuz berdi: {str(e)}"
# from google import genai
# from django.conf import settings
#
#
# def ai_handler(prompt_text):
#     api_key = getattr(settings, 'GEMINI_API_KEY', None)
#
#     if not api_key:
#         return "Xatolik: GEMINI_API_KEY topilmadi. .env faylingizni tekshiring."
#
#     try:
#         # Yangi google-genai mijozi
#         client = genai.Client(api_key=api_key)
#
#         response = client.models.generate_content(
#             model="gemini-3.6-flash",
#             contents=prompt_text,
#             config={
#                 "system_instruction": "Siz professional diyetolog va shaxsiy fitnes trenergiz. Javoblaringizni o'zbek tilida bering."
#             }
#         )
#         return response.text
#
#     except Exception as e:
#         return f"Gemini AI bilan bog'lanishda xatolik yuz berdi: {str(e)}"