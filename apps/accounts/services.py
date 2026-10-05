"""Accounts uchun umumiy servis funksiyalar.

Bu yerda Django'ga bog'liq, lekin aiogram/HTTP'ga bog'liq bo'lmagan mantiq
turadi. Shu sababli botdagi ro'yxatdan o'tish va bir martalik tokenni
oddiy Django testlari bilan tekshirish mumkin.
"""
import hashlib
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from .models import UserDetail, UsedLoginToken

PROFILE_CACHE_TTL = 900
TOKEN_RETENTION = timedelta(days=1)


class UsernameTakenError(Exception):
    """Tanlangan username band: mavjud hisobga hech narsa bog'lanmaydi."""


_username_validator = UnicodeUsernameValidator()


def username_taken(username: str) -> bool:
    """Registrga e'tibor bermasdan tekshiradi: 'Ali' va 'ali' bir xil hisoblanadi."""
    return User.objects.filter(username__iexact=username).exists()


def username_error(username: str):
    """Username noto'g'ri bo'lsa xabar qaytaradi, to'g'ri bo'lsa None."""
    if not username:
        return "Login bo'sh bo'lishi mumkin emas."
    if len(username) > 150:
        return "Login 150 belgidan oshmasligi kerak."
    try:
        _username_validator(username)
    except ValidationError:
        return "Loginda faqat harf, raqam va @ . + - _ belgilari bo'lishi mumkin."
    return None


def password_error(password: str):
    """Parol Django validatorlaridan o'tmasa birinchi xabarni qaytaradi."""
    try:
        validate_password(password)
    except ValidationError as exc:
        return exc.messages[0]
    return None


def get_user_profile(user):
    """Foydalanuvchi profilini keshdan yoki DB dan olish."""
    if not user or not user.is_authenticated:
        return None

    cache_key = f"user_profile_{user.id}"
    profile = cache.get(cache_key)

    if profile is None:
        profile = UserDetail.objects.filter(user=user).first()
        if profile:
            cache.set(cache_key, profile, timeout=PROFILE_CACHE_TTL)

    return profile


def user_has_profile(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return UserDetail.objects.filter(Q(user=user) | Q(telegram_user=user)).exists()


def invalidate_user_profile_cache(user):
    if user and user.is_authenticated:
        cache.delete(f"user_profile_{user.id}")


def consume_login_token(token: str) -> bool:
    """Tokenni BIR MARTA ishlatilgan deb belgilaydi.

    True  - token birinchi marta ishlatilmoqda (kirishga ruxsat).
    False - token oldin ishlatilgan (rad etiladi).

    Holat DB da saqlanadi, shuning uchun ko'p workerli Gunicorn'da ham,
    kesh tozalansa ham, jarayon qayta ishga tushsa ham kafolat saqlanadi.
    """
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    try:
        with transaction.atomic():
            UsedLoginToken.objects.create(token_hash=token_hash)
    except IntegrityError:
        return False

    # Eski yozuvlarni tozalash (token baribir 10 daqiqada eskiradi)
    UsedLoginToken.objects.filter(used_at__lt=timezone.now() - TOKEN_RETENTION).delete()
    return True


def register_telegram_user(telegram_id, username, password, data):
    """Telegram orqali ro'yxatdan o'tkazish (poygadan xavfsiz).

    Qoidalar:
    * Telegram ID allaqachon hisobga bog'langan bo'lsa, faqat ism-familiya
      yangilanadi (parol o'zgarmaydi).
    * Yangi User yaratishda username band bo'lsa (poyga holati ham) mavjud
      User QAYTA ISHLATILMAYDI: UsernameTakenError ko'tariladi.
    * Hamma amal bitta tranzaksiyada: xato bo'lsa yarim hisob qolmaydi.
    """
    with transaction.atomic():
        detail = (
            UserDetail.objects.select_related('user')
            .filter(telegram_id=telegram_id)
            .first()
        )

        if detail is not None and detail.user is not None:
            user = detail.user
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            user.save(update_fields=['first_name', 'last_name'])
        else:
            # 'Victim' va 'victim' ni ham bir xil deb hisoblaymiz (chalg'itib bo'lmasin)
            if username_taken(username):
                raise UsernameTakenError(username)
            try:
                # Ichki atomic = savepoint: IntegrityError tashqi tranzaksiyani buzmaydi
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=data.get('first_name', ''),
                        last_name=data.get('last_name', ''),
                    )
            except IntegrityError:
                raise UsernameTakenError(username)

            if detail is None:
                # Signal yaratgan bo'sh profilni olamiz
                detail, _ = UserDetail.objects.get_or_create(user=user)
            else:
                # Foydasiz (user'siz) eski profil bor: signal yaratgan bo'sh
                # profilni o'chirib, eskisini yangi user'ga biriktiramiz
                UserDetail.objects.filter(user=user).exclude(pk=detail.pk).delete()
                detail.user = user

        detail.telegram_id = telegram_id
        detail.first_name = data.get('first_name')
        detail.last_name = data.get('last_name')
        detail.phone_number = data.get('phone_number')
        detail.save()

    invalidate_user_profile_cache(user)
    return user
