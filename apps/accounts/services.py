"""
Butun loyiha bo'ylab UserDetail profilini topish uchun UMUMIY yordamchi
funksiya. Ilgari bir xil "user= bo'yicha, topilmasa telegram_user= bo'yicha
izlash" mantiqi accounts/views.py, fitness_app/views.py (4 marta) va
context_processors.py fayllarida alohida-alohida, har birida kamida
1-2 ta DB so'rovi bilan takrorlanardi. Endi bitta joyda, select_related
bilan bitta so'rovda ishlaydi.
"""
from django.db.models import Q
from django.core.cache import cache
from .models import UserDetail


def get_user_profile(user):
    """
    Foydalanuvchi profilini keshdan yoki DB dan olish.
    """
    if not user or not user.is_authenticated:
        return None

    cache_key = f"user_profile_{user.id}"
    profile = cache.get(cache_key)

    if profile is None:
        profile = UserDetail.objects.filter(user=user).first()
        if profile:
            # Profilni 15 daqiqaga keshga saqlaymiz
            cache.set(cache_key, profile, timeout=900)

    return profile


def user_has_profile(user) -> bool:
    """Faqat mavjudligini tekshirish kerak bo'lgan joylar uchun (masalan
    context_processor) — to'liq obyektni yuklamasdan, tezroq."""
    if not user or not user.is_authenticated:
        return False
    return UserDetail.objects.filter(Q(user=user) | Q(telegram_user=user)).exists()