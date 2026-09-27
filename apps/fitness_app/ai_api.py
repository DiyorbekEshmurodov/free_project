import json
import os
from groq import Groq
from django.conf import settings

PERIOD_LABELS = {'daily': 'kunlik', 'weekly': 'haftalik', 'monthly': 'oylik', 'yearly': 'yillik'}


def _fallback_advice(profile, card_id, period):
    """GROQ_API_KEY sozlanmagan yoki API xatolik bergan holatlar uchun
    zaxira matn. Ilgari bu matnlar apps/fitness_app/views.py ichida
    alohida, dublikat metod sifatida yozilgan edi va u yerda 'boyi' deb
    xato yozilgani uchun foydalanuvchining haqiqiy bo'yi hech qachon
    ishlatilmas edi ('buyi' — to'g'ri model maydoni nomi)."""
    vazni = getattr(profile, 'vazni', '70') if profile else '70'
    buyi = getattr(profile, 'buyi', '175') if profile else '175'
    try:
        vazn_num = float(vazni)
    except (ValueError, TypeError):
        vazn_num = 70.0

    p_name = PERIOD_LABELS.get(period, 'haftalik')

    if card_id == 'weight_loss':
        return {
            'nutrition': f"Sizning {p_name} ratsioningiz: Kuniga kamida {vazn_num * 35 / 1000:.1f}L suv iching. Shirinlik va xamir ovqatlarni butunlay cheklab, har bir taomlanishda 30g oqsil (tovuq go'shti, tuxum, tvorog) va murakkab uglevodlar (guruch, grechka) iste'mol qiling.",
            'workout': f"Sizning {p_name} mashg'ulot rejangiz: Boshlanishiga {p_name} 3-4 marta kardio (30 daqiqa yugurish yoki tez yurish) hamda umumiy tana mushaklarini mustahkamlovchi yengil kuch mashqlarini bajaring.",
            'ai_recommendation': f"Bo'yingiz {buyi} sm va vazningiz {vazni} kg bo'lgani uchun, metabolizmni ushlab turish muhim. Oqsillar balansi va 8 soatlik sifatli uyqu {p_name} rejangizning asosiy kalitidir.",
            'timeline': f"Ushbu {p_name} rejaga qat'iy amal qilsangiz, belgilangan vaqt davomida yog' foizini 2-4% ga kamaytirish va umumiy energiyani oshirish kafolatlanadi."
        }
    elif card_id == 'muscle_gain':
        return {
            'nutrition': f"Sizning {p_name} gipertrofiya ratsioningiz: Kunlik {vazn_num * 1.8:.0f}g oqsil qabul qiling. Kaloriya miqdorini normadan 300 kcal ga oshiring. Mol go'shti, baliq, tuxum va yong'oqlarga urg'u bering.",
            'workout': f"Sizning {p_name} mashg'ulot rejangiz: Og'ir vaznlar bilan 8-12 marta qaytariladigan bazaviy mashqlarni bajaring (Jim leja, Pritsed, Stanovaya tyaga). Har bir mashq orasida 2 daqiqa dam oling.",
            'ai_recommendation': f"Vazn {vazni} kg ko'rsatkichida mushak o'sishi uchun har bir mushak guruhiga mashqdan so'ng kamida 48 soat tiklanish vaqti bering.",
            'timeline': f"{p_name.capitalize()} natija: Mushak hajmining sezilarli darajada kattalashishi hamda kuch ko'rsatkichlarining 15-20% ga oshishi."
        }
    elif card_id == 'stamina':
        return {
            'nutrition': f"Sizning {p_name} energiya ratsioningiz: Antioksidantlarga boy mahsulotlar (suyak sho'rva, mevalar, ko'katlar) va yetarli miqdorda kaliy/magniy moddalarini qabul qiling.",
            'workout': f"Sizning {p_name} mashq rejangiz: Tabata va HIIT (Yuqori intensivli) mashqlarini bajaring. Yugurish masofasini va sur'atini {p_name} bosqichma-bosqich oshirib boring.",
            'ai_recommendation': "Nafas olish va yurak urish maromini (puls) nazorat qiling. Mashq paytida suvsizlanishga yo'l qo'ymang.",
            'timeline': f"{p_name.capitalize()} natija: Nafas qisishi yo'qolishi, quvvat darajasi va chidamlilikning maksimumga chiqishi."
        }
    else:  # health_habits
        return {
            'nutrition': f"Sizning {p_name} sog'lom ratsioningiz: Ishlov berilgan (fast-food, gazli ichimliklar) mahsulotlarni to'xtating. Har bir taomga yangi uzilgan sabzavotlar qo'shing.",
            'workout': f"Sizning {p_name} odat rejangiz: Kuniga kamida 8,000-10,000 qadam piyoda yuring, ertalabki 10 daqiqalik badan tarbiya va stretching mashqlarini bajaring.",
            'ai_recommendation': "Kun tartibiga amal qiling: Har kuni bir xil vaqtda uxlash va bir xil vaqtda uyg'onishni odat qiling.",
            'timeline': f"{p_name.capitalize()} natija: Uyqu sifatining yaxshilanishi, hazm qilish tizimi normallashishi va kayfiyat barqarorligi."
        }
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