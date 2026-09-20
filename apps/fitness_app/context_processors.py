def user_profile_status(request):
    from accounts.models import UserDetail
    has_profile = False
    if request.user.is_authenticated:
        # Foydalanuvchida UserDetail mavjudligi va to'ldirilganini tekshirish
        has_profile = UserDetail.objects.filter(user=request.user).exists()

    return {
        'has_profile': has_profile
    }