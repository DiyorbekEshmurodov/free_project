from .models import FitnessPlan

def get_plans_by_period(user_id, period):
    """
    Foydalanuvchi ID si va reja turiga (kunlik, haftalik, oylik, yillik)
    qarab ma'lumotlarni filtrlab beradi.
    """
    try:
        # UserDetail_id o'rniga Django'ning standart modeldagi user_id ishlatiladi
        plans = list(FitnessPlan.objects.filter(user_id=user_id, period_type=period).values())
        return plans if plans else False
    except Exception:
        return False

def get_all_hisobot(user_id):
    """
    Berilgan foydalanuvchining barcha turdagi reja va hisobotlarini olib keladi.
    """
    hisobotlar = list(FitnessPlan.objects.filter(user_id=user_id).values())
    if not hisobotlar:
        return False
    return hisobotlar


