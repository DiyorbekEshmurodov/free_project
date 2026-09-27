from .models import UserDetail
from .forms import UserDetailForm
from .services import get_user_profile

from django.contrib.auth.models import User
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.cache import cache


def _get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def _too_many_login_attempts(request):
    """Tashqi qo'shimcha kutubxonasiz, Django cache orqali sodda
    brute-force himoyasi: bir IP 1 daqiqada 5 martadan ko'p muvaffaqiyatsiz
    login urinishi qilsa, vaqtincha bloklanadi."""
    cache_key = f"login_attempts:{_get_client_ip(request)}"
    attempts = cache.get(cache_key, 0)
    return attempts >= 5


def _register_failed_login_attempt(request):
    cache_key = f"login_attempts:{_get_client_ip(request)}"
    attempts = cache.get(cache_key, 0)
    cache.set(cache_key, attempts + 1, timeout=60)  # 60 soniyalik oyna


def _clear_login_attempts(request):
    cache.delete(f"login_attempts:{_get_client_ip(request)}")


@login_required
def dashboard_view(request):
    # Ilgari bu yerda 2 marta alohida so'rov yuborilardi
    # (user= bo'yicha, topilmasa telegram_user= bo'yicha) — endi bitta
    # umumiy funksiya orqali, 1 ta so'rov bilan.
    profil = get_user_profile(request.user)

    has_profile = False

    if profil:
        # String ga o'tkazib, bo'shliqlarni tozalaymiz (strip)
        buyi_val = str(profil.buyi).strip() if profil.buyi is not None else ""
        vazni_val = str(profil.vazni).strip() if profil.vazni is not None else ""

        # Gar ushbu qiymatlar bo'sh bo'lmasa va 'None' so'zi bo'lmasa True bo'ladi
        if buyi_val and vazni_val and buyi_val != "None" and vazni_val != "None":
            has_profile = True

    context = {
        'profil': profil,
        'has_profile': has_profile,
    }
    return render(request, 'index.html', context)


def auto_login_view(request, token):
    """
        Xavfsiz bir martalik token orqali kirish (Telegram ID o'rniga token ishlatiladi).
        Token 10 daqiqa (600 soniya) davomida amal qiladi.
    """
    signer = TimestampSigner()
    try:
        # Tokenni tekshirish va undan telegram_id ni ajratib olish (max_age = 600 soniya)
        telegram_id = signer.unsign(token, max_age=600)
        profil = UserDetail.objects.filter(telegram_id=telegram_id).first()

        if profil and profil.user:
            login(request, profil.user)
            return redirect('index')
        else:
            messages.error(request, "Foydalanuvchi profili topilmadi.")
            return redirect('login_page')

    except (SignatureExpired, BadSignature):
        messages.error(request, "Kirish havolasining vaqti o'tgan yoki havola noto'g'ri!")
        return redirect('login_page')

def login_required_decorator(func):
    return login_required(func,login_url='login_page')

@login_required_decorator
def logout_page(request):
    logout(request)
    return redirect('home')

@login_required_decorator
def profile_setup(request):
    profile, created = UserDetail.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserDetailForm(request.POST, request.FILES,instance=profile)
        if form.is_valid():
            form.save()
            # Avval bu yerda request.POST dan to'g'ridan-to'g'ri o'qilardi —
            # bu forma validatsiyasini (uzunlik chegarasi va h.k.) chetlab
            # o'tar edi. UserDetailForm'da first_name/last_name allaqachon
            # bor va tekshirilgan, shuning uchun form.cleaned_data ishlatiladi.
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
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone_number = request.POST.get('phone')

        if action_type == 'login':
            if _too_many_login_attempts(request):
                messages.error(
                    request,
                    "Juda ko'p noto'g'ri urinish qilindi. Iltimos, 1 daqiqadan "
                    "so'ng qaytadan urinib ko'ring."
                )
                return render(request, 'accounts/login.html')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                _clear_login_attempts(request)
                login(request, user)
                return redirect('index')
            else :
                _register_failed_login_attempt(request)
                return render(request,'accounts/login.html',{'error':'Username yoki parol xato kiritilgan\nQaytadan kiriting 😁 '})


        elif action_type == 'register':

            has_upper = any(char.isupper() for char in password)
            has_lower = any(char.islower() for char in password)
            if password != confirm_password:
                messages.error(request, 'Parollar bir xil emas!')
            elif len(password) < 8 or not has_upper or not has_lower:
                messages.error(request,
                'Parol kamida 8 ta belgi, 1 ta katta va 1 ta kichik harfdan iborat bo\'lishi kerak!')
            elif User.objects.filter(username=username).exists():
                    messages.error(request,'Bunday Foydalanuvchi alloqachon mavjud!')
            else:
                new_user = User.objects.create_user(username=username,password=password)
                new_user.save()
                login(request, new_user)
                return redirect('index')

        elif action_type == 'reset':
            confirm_password = request.POST.get('confirm_password')
            try:
                user = User.objects.get(username=username)
                has_upper = any(char.isupper() for char in password)
                has_lower = any(char.islower() for char in password)

                # Avvalgi kodda bu ikki tekshiruv alohida if bloklarida edi va
                # pastdagi "if password == confirm_password" shartini
                # to'xtatmas edi — natijada zaif, lekin bir-biriga mos parol
                # baribir saqlanib qolardi. Endi bitta if/elif/else zanjiri:
                if password != confirm_password:
                    messages.error(request, 'Parollar bir xil emas!')
                elif len(password) < 8 or not has_upper or not has_lower:
                    messages.error(
                        request,
                        "Yangi parol kamida 8 ta belgi, 1 ta katta va 1 ta kichik "
                        "harfdan iborat bo'lishi kerak!"
                    )
                else:
                    # Faqat HAR IKKALA shart (mosligi + kuchliligi) bajarilganda saqlanadi
                    user.set_password(password)
                    user.save()
                    login(request, user)
                    return redirect('index')
            except User.DoesNotExist:
                messages.error(request, 'Parolni tiklash uchun qaytadan kiring!')

    return render(request,'accounts/login.html')



def main_account(request):
    return render(request,'home.html')

def index_page(request):
    return dashboard_view(request)