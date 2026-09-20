from django.shortcuts import render
from .services import ai_handler
from .models import UserQuestion
from .prompts import SECTION_MAP
from accounts.models import UserDetail
# 1. BARCHA KARTALAR RO'YXATI UCHUN UNIVERSAL VIEW
def cards_list_view(request, section_name):
    section_data = SECTION_MAP.get(section_name)

    profil = None
    if request.user.is_authenticated:
        profil = UserDetail.objects.filter(user=request.user).first()

    ctx = {
        'section_name': section_name,
        'title': section_data['title'],
        'subtitle': section_data['subtitle'],
        'questions': section_data['questions'],
        'profil': profil,
        'has_profile': profil is not None,
    }
    return render(request, 'ai_app/cards.html', ctx)


# 2. TANLANGAN KARTA DETAIL KUNI UCHUN UNIVERSAL VIEW
def card_detail_view(request, section_name, question_id):
    section_data = SECTION_MAP.get(section_name)
    question_data = section_data['questions'].get(question_id)

    profil = None
    user_info = None
    if request.user.is_authenticated:
        profil = UserDetail.objects.filter(user=request.user).last()
        user_info = UserQuestion.objects.filter(user=request.user).last()

    # Agar foydalanuvchi ma'lumotlari bo'lsa ularni, bo'lmasa standart qiymatlarni uzatamiz
    buyi = getattr(profil, 'buyi', None) or getattr(user_info, 'buyi', None) or 170
    vazni = getattr(profil, 'vazni', None) or getattr(user_info, 'vazni', None) or 70
    maqsadi = getattr(profil, 'maqsadi', None) or getattr(user_info, 'maqsadi', None) or "Sog'lom turmush tarzi"

    card_title = question_data.get('title', '')
    card_desc = question_data.get('short_desc', '')

    full_prompt = (
        f"Mavzu: {card_title}\n"
        f"Tavsif: {card_desc}\n"
        f"Foydalanuvchi ko'rsatkichlari: Bo'yi: {buyi} sm, Vazni: {vazni} kg, Maqsadi: {maqsadi}.\n\n"
        f"Vazifa: Ushbu foydalanuvchiga tanlangan mavzu bo'yicha uning ko'rsatkichlariga mos amaliy va aniq maslahat bering."
    )

    ai_result = ai_handler(full_prompt)

    ctx = {
        'section_name': section_name,
        'question_data': question_data,
        'ai_result': ai_result,
        'profil': profil,
        'has_profile': profil is not None,
    }

    return render(request, 'ai_app/card_detail.html', ctx)
