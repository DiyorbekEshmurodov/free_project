import hashlib
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import UserDetailForm
from .models import UserDetail
from .services import (
    consume_login_token,
    get_user_profile,
    invalidate_user_profile_cache,
    password_error,
    username_error,
    username_taken,
)

logger = logging.getLogger('security')

MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCK_SECONDS = 300
AUTO_LOGIN_MAX_AGE = 600


def _get_client_ip(request):
    """Mijoz IP manzili.

    X-Forwarded-For ni mijozning o'zi ham yuborishi mumkin, shuning uchun
    CHAPDAGI (birinchi) qiymatga ishonib bo'lmaydi. Ishonchli proksi
    (nginx, Render) o'zi ko'rgan IP ni ro'yxatning OXIRIGA qo'shadi.
    NUM_PROXIES = bizning oldimizdagi ishonchli proksilar soni:
    0 - header o'qilmaydi (REMOTE_ADDR), 1 - oxirgi qiymat, 2 - oxiridan ikkinchisi.
    """
    num_proxies = getattr(settings, 'NUM_PROXIES', 0)
    if num_proxies > 0:
        parts = [p.strip() for p in request.META.get('HTTP_X_FORWARDED_FOR', '').split(',') if p.strip()]
        if len(parts) >= num_proxies:
            return parts[-num_proxies]
    return request.META.get('REMOTE_ADDR', 'unknown')


def _attempts_key(request, username):
    # username ni hash qilamiz: kalit uzunligi cheklangan va begona belgisiz bo'ladi
    digest = hashlib.sha256(username.lower().encode('utf-8')).hexdigest()[:32]
    return f"login_attempts:{_get_client_ip(request)}:{digest}"


def _too_many_login_attempts(request, username=""):
    return cache.get(_attempts_key(request, username), 0) >= MAX_LOGIN_ATTEMPTS


def _register_failed_login_attempt(request, username=""):
    key = _attempts_key(request, username)
    cache.set(key, cache.get(key, 0) + 1, timeout=LOGIN_LOCK_SECONDS)


def _clear_login_attempts(request, username=""):
    cache.delete(_attempts_key(request, username))


@login_required
def dashboard_view(request):
    profil = get_user_profile(request.user)
    has_profile = bool(profil and profil.is_profile_complete)
    return render(request, 'index.html', {'profil': profil, 'has_profile': has_profile})


def auto_login_view(request, token):
    """Telegram orqali imzolangan, bir martalik va muddatli kirish havolasi."""
    signer = TimestampSigner(salt='lifegym.autologin')
    try:
        telegram_id = signer.unsign(token, max_age=AUTO_LOGIN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        logger.warning("auto-login rad etildi: imzo noto'g'ri yoki muddat o'tgan (ip=%s)", _get_client_ip(request))
        messages.error(request, "Kirish havolasining vaqti o'tgan yoki havola noto'g'ri!")
        return redirect('login_page')

    # Bir martalik kafolat umumiy ombor (DB) orqali - barcha workerlarda ishlaydi
    if not consume_login_token(token):
        logger.warning("auto-login rad etildi: token qayta ishlatildi (ip=%s)", _get_client_ip(request))
        messages.error(request, "Ushbu kirish havolasidan allaqachon foydalanilgan!")
        return redirect('login_page')

    profil = UserDetail.objects.select_related('user').filter(telegram_id=telegram_id).first()
    if profil and profil.user and profil.user.is_active:
        login(request, profil.user)
        return redirect('index')

    messages.error(request, "Foydalanuvchi profili topilmadi yoki hisob faol emas.")
    return redirect('login_page')


@require_POST
@login_required
def logout_page(request):
    """Logout faqat POST (+CSRF token) orqali bajariladi."""
    logout(request)
    return redirect('home')


@login_required
def profile_setup(request):
    profile, _ = UserDetail.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserDetailForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            invalidate_user_profile_cache(request.user)
            request.user.first_name = form.cleaned_data.get('first_name') or request.user.first_name
            request.user.last_name = form.cleaned_data.get('last_name') or request.user.last_name
            request.user.save(update_fields=['first_name', 'last_name'])
            messages.success(request, "Ma'lumotlaringiz muvaffaqiyatli saqlandi!")
            return redirect('index')
    else:
        form = UserDetailForm(instance=profile)

    return render(request, 'accounts/profile.html', {'form': form})


def login_page(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if action_type == 'login':
            if _too_many_login_attempts(request, username):
                logger.warning("login bloklandi: juda ko'p urinish (ip=%s)", _get_client_ip(request))
                messages.error(request, "Juda ko'p noto'g'ri urinish qilindi. 5 daqiqadan so'ng qayta urinib ko'ring.")
                return render(request, 'accounts/login.html')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                _clear_login_attempts(request, username)
                login(request, user)
                return redirect('index')
            _register_failed_login_attempt(request, username)
            logger.info("login muvaffaqiyatsiz (ip=%s)", _get_client_ip(request))
            return render(request, 'accounts/login.html', {'error': "Username yoki parol xato kiritilgan!"})

        elif action_type == 'register':
            confirm_password = request.POST.get('confirm_password', '')
            has_upper = any(char.isupper() for char in password)
            has_lower = any(char.islower() for char in password)

            if password != confirm_password:
                messages.error(request, 'Parollar bir xil emas!')
            elif len(password) < 8 or not has_upper or not has_lower:
                messages.error(request,
                               "Parol kamida 8 ta belgi, 1 ta katta va 1 ta kichik harfdan iborat bo'lishi kerak!")
            elif username_error(username):
                messages.error(request, username_error(username))
            elif password_error(password):
                messages.error(request, password_error(password))
            elif username_taken(username):
                messages.error(request, 'Bunday foydalanuvchi allaqachon mavjud!')
            else:
                try:
                    new_user = User.objects.create_user(username=username, password=password)
                except IntegrityError:
                    # Tekshiruv bilan yozuv orasidagi poyga: 500 emas, xabar
                    messages.error(request, 'Bunday foydalanuvchi allaqachon mavjud!')
                else:
                    login(request, new_user)
                    return redirect('index')

        # Tizimga kirmagan holatda vebdan parol tiklash o'chirilgan
        elif action_type == 'reset':
            messages.error(request, "Parolni tiklash faqat Telegram bot orqali amalga oshiriladi.")

    return render(request, 'accounts/login.html')


def main_account(request):
    return render(request, 'home.html')


def index_page(request):
    return dashboard_view(request)
