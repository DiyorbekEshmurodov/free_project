from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.cache import cache
from django.contrib.auth.models import User

from .models import UserDetail
from .forms import UserDetailForm
from .services import get_user_profile


def _get_client_ip(request):
    """Proksi ortidagi IP ni to'g'ri va xavfsiz olish (B5)."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def _too_many_login_attempts(request, username=""):
    """IP va Username bo'yicha login cheklovini hisoblash (B5)."""
    ip = _get_client_ip(request)
    cache_key = f"login_attempts:{ip}:{username}"
    attempts = cache.get(cache_key, 0)
    return attempts >= 5


def _register_failed_login_attempt(request, username=""):
    ip = _get_client_ip(request)
    cache_key = f"login_attempts:{ip}:{username}"
    attempts = cache.get(cache_key, 0)
    cache.set(cache_key, attempts + 1, timeout=300)


def _clear_login_attempts(request, username=""):
    ip = _get_client_ip(request)
    cache.delete(f"login_attempts:{ip}:{username}")


@login_required
def dashboard_view(request):
    profil = get_user_profile(request.user)
    has_profile = False

    if profil:
        buyi_val = str(profil.buyi).strip() if profil.buyi is not None else ""
        vazni_val = str(profil.vazni).strip() if profil.vazni is not None else ""
        if buyi_val and vazni_val and buyi_val != "None" and vazni_val != "None":
            has_profile = True

    return render(request, 'index.html', {'profil': profil, 'has_profile': has_profile})


def auto_login_view(request, token):
    """B2: Salt qo'shilgan va kesh orqali bir martalik qilingan auto-login."""
    signer = TimestampSigner(salt='lifegym.autologin')
    try:
        telegram_id = signer.unsign(token, max_age=600)
    except (BadSignature, SignatureExpired):
        messages.error(request, "Kirish havolasining vaqti o'tgan yoki havola noto'g'ri!")
        return redirect('login_page')

    used_key = f"used_autologin_token_{token}"
    if not cache.add(used_key, "true", timeout=600):
        messages.error(request, "Ushbu kirish havolasidan allaqachon foydalanilgan!")
        return redirect('login_page')

    profil = UserDetail.objects.filter(telegram_id=telegram_id).first()
    if profil and profil.user and profil.user.is_active:
        login(request, profil.user)
        return redirect('index')

    messages.error(request, "Foydalanuvchi profili topilmadi yoki hisob faol emas.")
    return redirect('login_page')


@require_POST
@login_required
def logout_page(request):
    """B8: Logout faqat POST so'rovi orqali bajariladi."""
    logout(request)
    return redirect('home')


@login_required
def profile_setup(request):
    profile, _ = UserDetail.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserDetailForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
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
                messages.error(request, "Juda ko'p noto'g'ri urinish qilindi. 5 daqiqadan so'ng qayta urinib ko'ring.")
                return render(request, 'accounts/login.html')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                _clear_login_attempts(request, username)
                login(request, user)
                return redirect('index')
            else:
                _register_failed_login_attempt(request, username)
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
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'Bunday foydalanuvchi allaqachon mavjud!')
            else:
                new_user = User.objects.create_user(username=username, password=password)
                login(request, new_user)
                return redirect('index')

        # B1: Tizimga kirmagan holatda vebdan parol tiklash o'chirilgan
        elif action_type == 'reset':
            messages.error(request, "Parolni tiklash faqat Telegram bot orqali amalga oshiriladi.")

    return render(request, 'accounts/login.html')


def main_account(request):
    return render(request, 'home.html')


def index_page(request):
    return dashboard_view(request)