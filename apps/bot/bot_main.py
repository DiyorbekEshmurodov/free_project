import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
import logging
from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup,KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from apps.accounts.models import UserDetail
from django.contrib.auth.models import User
from django.core.signing import TimestampSigner
from asgiref.sync import sync_to_async
from . import globals
from .states import LoginStates


main_router = Router()
signer = TimestampSigner()
logger = logging.getLogger(__name__)


def build_auto_login_url(telegram_id: int) -> str:
    """Telegram ID ni xavfsiz, vaqt bilan cheklangan tokenga aylantirib,
    auto-login havolasini yaratadi."""
    signed_token = signer.sign(str(telegram_id))
    return f"https://lifegym-kapp.onrender.com/auto-login/{signed_token}/"


phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


@sync_to_async
def get_user_detail(telegram_id):
    return UserDetail.objects.filter(telegram_id=telegram_id).select_related('user').first()


@sync_to_async
def check_username_exists(username):
    # UserDetail modelida 'username' maydoni yo'q — Django User modeli
    # bo'yicha tekshirilishi kerak, aks holda FieldError bilan crash beradi.
    return User.objects.filter(username=username).exists()


@sync_to_async
def save_user_registration_data(telegram_id, username_input, password, data):
    # 1. Shu telegram_id bilan bog'liq profil (agar avval boshlangan bo'lsa) izlanadi
    user_detail = UserDetail.objects.filter(telegram_id=telegram_id).first()

    if user_detail and user_detail.user:
        # Profil va unga bog'langan User allaqachon mavjud — shunchaki yangilaymiz
        user = user_detail.user
        user.username = username_input
        user.set_password(password)
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')
        user.save()
    else:
        existing_user = User.objects.filter(username=username_input).first()

        if existing_user:
            user = existing_user
            user.set_password(password)
            user.first_name = data.get('first_name', '')
            user.last_name = data.get('last_name', '')
            user.save()
        else:
            # Yangi User yaratiladi. DIQQAT: bu chaqiruv post_save signalini
            # ishga tushiradi va signal AVTOMATIK ravishda UserDetail(user=user)
            # qatorini yaratadi — shuning uchun bu yerda o'zimiz alohida
            # UserDetail.objects.create(...) qilmaymiz, aks holda dublikat
            # paydo bo'lardi.
            user = User.objects.create_user(
                username=username_input,
                password=password,
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', '')
            )

        # Signal (yoki avvalgi ro'yxatdan o'tish) allaqachon yaratgan yagona
        # profilni topib, aynan O'SHANI ishlatamiz — yangi qator OCHMAYMIZ.
        if user_detail is None:
            user_detail, _ = UserDetail.objects.get_or_create(user=user)

    # 2. Yagona UserDetail qatoriga barcha ma'lumotlarni yozamiz
    user_detail.telegram_id = telegram_id
    user_detail.telegram_user = user
    user_detail.user = user
    user_detail.first_name = data.get('first_name')
    user_detail.last_name = data.get('last_name')
    user_detail.phone_number = data.get('phone_number')
    user_detail.save()


@main_router.message(Command('start'))
async def start(message: types.Message, state: FSMContext):
    await message.answer(globals.WELCOME_TEXT)
    user_telegram_id = message.from_user.id
    site_url = build_auto_login_url(user_telegram_id)

    user_detail = await get_user_detail(user_telegram_id)
    # AGAR USER MAVJUD BO'LSA - Shunchaki saytga havola beramiz
    if user_detail and user_detail.user:
        buttons = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="Life Gym Saytiga O'tish",
                    url=site_url
                )
            ]]
        )
        await message.answer(
            f"Salom, {user_detail.first_name or 'foydalanuvchi'}! Siz allaqachon ro'yxatdan o'tgansiz.",
            reply_markup=buttons
        )
        return

    # ELSE (Ro'yxatdan o'tmagan bo'lsa) - Ro'yxatdan o'tkazishni boshlaymiz
    await state.set_state(LoginStates.first_name)
    await message.answer(globals.TEXT_ENTER_FIRST_NAME)


@main_router.message(LoginStates.first_name)
async def first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await state.set_state(LoginStates.last_name)
    await message.answer(globals.TEXT_ENTER_LAST_NAME)


@main_router.message(LoginStates.last_name)
async def last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await state.set_state(LoginStates.phone_number)
    await message.answer(globals.TEXT_ENTER_CONTACT, reply_markup=phone_keyboard)


@main_router.message(LoginStates.phone_number)
async def phone_number(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone_number=phone)

    await state.set_state(LoginStates.username)
    await message.answer("Saytga kirish uchun **Login (Username)** kiriting:", reply_markup=ReplyKeyboardRemove())


@main_router.message(LoginStates.username)
async def process_username(message: types.Message, state: FSMContext):
    username = message.text.strip()
    is_exists = await check_username_exists(username)
    if is_exists:
        await message.answer("Ushbu login band! Iltimos, boshqa login kiriting:")
        return

    await state.update_data(username=username)
    await state.set_state(LoginStates.password)
    await message.answer("Saytga kirish uchun **Parol** o'ylab toping va kiriting:")


@main_router.message(LoginStates.password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    has_upper = any(char.isupper() for char in password)
    has_lower = any(char.islower() for char in password)
    if len(password) < 8 or not has_upper or not has_lower:
        await message.answer(
            "❌ **Parol talablarga javob bermaydi!**\n\n"
            "Parol kamida 8 ta belgidan iborat bo'lishi, hamda kamida 1 ta katta harf (A-Z) va 1 ta kichik harf (a-z) qatnashishi kerak.\n\n"
            "Iltimos, qaytadan boshqa parol kiriting:",
            parse_mode="Markdown"
        )
        return
    data = await state.get_data()
    telegram_id = message.from_user.id
    username_input = data.get('username')

    try:
        await save_user_registration_data(telegram_id, username_input, password, data)
        await state.clear()
        site_url = build_auto_login_url(telegram_id)
        buttons = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="Life Gym Saytiga O'tish",
                    url=site_url
                )
            ]]
        )

        await message.answer(
            f"✅ **Muvaffaqiyatli saqlandi!**\n\n"
            f"🔑 **Loginingiz:** `{username_input}`\n\n"
            f"🔒 Parolingizni siz o'zingiz kiritgansiz — uni xavfsiz joyda saqlang "
            f"va hech kimga bermang (bot uni chatda qayta ko'rsatmaydi).\n\n"
            f"Endi ushbu login va parolingiz bilan saytga kirishingiz mumkin.",
            reply_markup=buttons,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Foydalanuvchini ro'yxatdan o'tkazishda xatolik: {e}")
        await message.answer("❌ Saqlashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")