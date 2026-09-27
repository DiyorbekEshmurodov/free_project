"""
Butun loyiha bo'ylab UserDetail profilini topish uchun UMUMIY yordamchi
funksiya. Ilgari bir xil "user= bo'yicha, topilmasa telegram_user= bo'yicha
izlash" mantiqi accounts/views.py, fitness_app/views.py (4 marta) va
context_processors.py fayllarida alohida-alohida, har birida kamida
1-2 ta DB so'rovi bilan takrorlanardi. Endi bitta joyda, select_related
bilan bitta so'rovda ishlaydi.
"""
from django.db.models import Q
from .models import UserDetail


def get_user_profile(user):
    """Berilgan Django User uchun bog'liq UserDetail profilini qaytaradi
    (avval 'user' FK, keyin 'telegram_user' FK bo'yicha), topilmasa None."""
    if not user or not user.is_authenticated:
        return None
    return (
        UserDetail.objects
        .select_related('user', 'telegram_user')
        .filter(Q(user=user) | Q(telegram_user=user))
        .order_by('-id')
        .first()
    )


def user_has_profile(user) -> bool:
    """Faqat mavjudligini tekshirish kerak bo'lgan joylar uchun (masalan
    context_processor) — to'liq obyektni yuklamasdan, tezroq."""
    if not user or not user.is_authenticated:
        return False
    return UserDetail.objects.filter(Q(user=user) | Q(telegram_user=user)).exists()