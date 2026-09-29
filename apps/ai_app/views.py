from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.contrib.auth.decorators import login_required

from .services import get_cached_llm_completion
from .models import UserQuestion
from .prompts import SECTION_MAP
from apps.accounts.models import UserDetail
from apps.accounts.services import get_user_profile


@login_required
def cards_list_view(request, card_id):
    """1. Barcha kartalar ro'yxatini ko'rish view'si."""
    card = get_object_or_404(id=card_id)

    # A1: question_data va None tekshiruvi
    question_data = card.get_question_data()
    if question_data is None:
        raise Http404("So'ralgan savol ma'lumotlari topilmadi.")

    profil = get_user_profile(request.user)

    ctx = {
        'card': card,
        'question_data': question_data,
        'profil': profil,
        'has_profile': profil is not None,
    }
    return render(request, 'ai_app/cards.html', ctx)


@login_required
def card_detail_view(request, section_name, question_id):
    """2. Tanlangan karta tafsilotlarini ko'rish view'si."""
    section_data = SECTION_MAP.get(section_name)
    if section_data is None:
        raise Http404('Bunday bo\'lim topilmadi')

    question_data = section_data.get('questions', {}).get(question_id)
    if question_data is None:
        raise Http404('Bunday savol topilmadi')

    profil = get_user_profile(request.user)
    user_info = UserQuestion.objects.filter(user=request.user).last()

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

    # C1: Kesh va taymautga ega LLM chaqiruvi
    ai_result = get_cached_llm_completion(full_prompt)

    ctx = {
        'section_name': section_name,
        'question_data': question_data,
        'ai_result': ai_result,
        'profil': profil,
        'has_profile': profil is not None,
    }

    return render(request, 'ai_app/card_detail.html', ctx)