from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from apps.accounts.services import get_user_profile

from .prompts import SECTION_MAP
from .services import get_cached_llm_completion


def _get_section_or_404(section_name):
    section = SECTION_MAP.get(section_name)
    if section is None:
        raise Http404("Bunday bo'lim topilmadi")
    return section


@login_required
def cards_list_view(request, section_name):
    """Tanlangan bo'lim kartalari ro'yxati (URL kwarg: section_name)."""
    section = _get_section_or_404(section_name)
    profil = get_user_profile(request.user)

    ctx = {
        'section_name': section_name,
        'title': section.get('title', ''),
        'subtitle': section.get('subtitle', ''),
        'questions': section.get('questions', {}),
        'profil': profil,
        'has_profile': profil is not None,
    }
    return render(request, 'ai_app/cards.html', ctx)


@login_required
def card_detail_view(request, section_name, question_id):
    """Tanlangan karta tafsilotlari + AI maslahati."""
    section = _get_section_or_404(section_name)
    question_data = section.get('questions', {}).get(question_id)
    if question_data is None:
        raise Http404("Bunday savol topilmadi")

    profil = get_user_profile(request.user)

    buyi = getattr(profil, 'buyi', None) or 170
    vazni = getattr(profil, 'vazni', None) or 70
    maqsadi = getattr(profil, 'maqsadi', None) or "Sog'lom turmush tarzi"

    full_prompt = (
        f"Mavzu: {question_data.get('title', '')}\n"
        f"Tavsif: {question_data.get('short_desc', '')}\n"
        f"Foydalanuvchi ko'rsatkichlari: Bo'yi: {buyi} sm, Vazni: {vazni} kg, Maqsadi: {maqsadi}.\n\n"
        "Vazifa: Ushbu foydalanuvchiga tanlangan mavzu bo'yicha umumiy, ehtiyotkor va amaliy "
        "maslahat bering. Natijani kafolatlamang; sog'liq muammosi bo'lsa shifokorga murojaat "
        "qilishni eslatib o'ting."
    )

    ai_result = get_cached_llm_completion(full_prompt, user_id=request.user.id)

    ctx = {
        'section_name': section_name,
        'question_data': question_data,
        'ai_result': ai_result,
        'profil': profil,
        'has_profile': profil is not None,
    }
    return render(request, 'ai_app/card_detail.html', ctx)
