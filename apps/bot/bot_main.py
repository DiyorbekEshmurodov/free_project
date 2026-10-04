import os
import logging
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup, \
    KeyboardButton
from aiogram.filters import Command
from asgiref.sync import sync_to_async
from aiogram.fsm.context import FSMContext


from django.conf import settings
from django.contrib.auth.models import User
from django.core.signing import TimestampSigner
from apps.accounts.models import UserDetail
from apps.accounts.services import UsernameTakenError, register_telegram_user
from . import globals
from .states import LoginStates

main_router = Router()
signer = TimestampSigner(salt='lifegym.autologin')
logger = logging.getLogger(__name__)


def build_auto_login_url(telegram_id: int) -> str:
    """B2: Salt bilan himoyalangan auto-login URL generatori."""
    signed_token = signer.sign(str(telegram_id))
    return f"{settings.SITE_URL.rstrip('/')}/auto-login/{signed_token}/"


phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)


@sync_to_async
def get_user_detail(telegram_id):
    return UserDetail.objects.filter(telegram_id=telegram_id).select_related('user').first()


@sync_to_async
def check_username_exists(username):
    return User.objects.filter(username=username).exists()


@sync_to_async
def save_user_registration_data(telegram_id, username_input, password, data):
    """Ro'yxatdan o'tkazish mantiqi accounts.services da (testlanadigan joyda).

    Username band bo'lsa UsernameTakenError ko'tariladi, mavjud hisobga
    Telegram ID BOG'LANMAYDI.
    """
    return register_telegram_user(telegram_id, username_input, password, data)


@main_router.message(Command('start'))
async def start(message: types.Message, state: FSMContext):
    await message.answer(globals.WELCOME_TEXT)
    user_telegram_id = message.from_user.id
    site_url = build_auto_login_url(user_telegram_id)

    user_detail = await get_user_detail(user_telegram_id)
    if user_detail and user_detail.user:
        buttons = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Life Gym Saytiga O'tish", url=site_url)]]
        )
        await message.answer(
            f"Salom, {user_detail.first_name or 'foydalanuvchi'}! Siz allaqachon ro'yxatdan o'tgansiz.",
            reply_markup=buttons
        )
        return

    await state.set_state(LoginStates.first_name)
    await message.answer(globals.TEXT_ENTER_FIRST_NAME)


@main_router.message(LoginStates.first_name, F.text)
async def first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await state.set_state(LoginStates.last_name)
    await message.answer(globals.TEXT_ENTER_LAST_NAME)


@main_router.message(LoginStates.last_name, F.text)
async def last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await state.set_state(LoginStates.phone_number)
    await message.answer(globals.TEXT_ENTER_CONTACT, reply_markup=phone_keyboard)


@main_router.message(LoginStates.phone_number, F.contact | F.text)
async def phone_number(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone_number=phone)

    await state.set_state(LoginStates.username)
    await message.answer("Saytga kirish uchun **Login (Username)** kiriting:", reply_markup=ReplyKeyboardRemove())


@main_router.message(LoginStates.username, F.text)
async def process_username(message: types.Message, state: FSMContext):
    username = message.text.strip()
    if not username:
        await message.answer("Login bo'sh bo'lishi mumkin emas. Iltimos, login kiriting:")
        return
    is_exists = await check_username_exists(username)
    if is_exists:
        await message.answer("Ushbu login band! Iltimos, boshqa login kiriting:")
        return

    await state.update_data(username=username)
    await state.set_state(LoginStates.password)
    await message.answer("Saytga kirish uchun **Parol** o'ylab toping va kiriting:")


@main_router.message(LoginStates.password, F.text)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text
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

        # B11: Xavfsizlik uchun foydalanuvchi kiritgan parol xabarini o'chirib tashlaymiz
        try:
            await message.delete()
        except Exception:
            pass

        site_url = build_auto_login_url(telegram_id)
        buttons = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Life Gym Saytiga O'tish", url=site_url)]]
        )

        await message.answer(
            f"✅ **Muvaffaqiyatli saqlandi!**\n\n"
            f"🔑 **Loginingiz:** `{username_input}`\n\n"
            f"🔒 Parolingiz saqlandi. Saytga kirishda ushbu ma'lumotlardan foydalaning.",
            reply_markup=buttons,
            parse_mode="Markdown"
        )

    except UsernameTakenError:
        # Tekshiruv va yozuv orasida login band bo'lib qoldi (poyga holati).
        # Mavjud hisobni ishlatmaymiz: ro'yxatdan o'tishni rad etib, yangi login so'raymiz.
        try:
            await message.delete()
        except Exception:
            pass
        await state.update_data(username=None)
        await state.set_state(LoginStates.username)
        await message.answer("Ushbu login band! Iltimos, boshqa login kiriting:")
    except Exception:
        logger.exception("Foydalanuvchini ro'yxatdan o'tkazishda xatolik")
        await message.answer("❌ Saqlashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")


# A3: Matn bo'lmagan (stiker, rasm) xabarlar uchun umumiy qaytaruvchi
@main_router.message(~F.text & ~F.contact)
async def handle_non_text_message(message: types.Message):
    await message.answer("Iltimos, faqat matnli xabar yuboring.")