from aiogram import Bot, Dispatcher ,Router,types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove,ReplyKeyboardMarkup,KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from accounts.models import UserDetail
from django.contrib.auth.models import User
from . import globals
from .states import LoginStates
main_router = Router()
phone_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


@main_router.message(Command('start'))
async def start(message: types.Message, state: FSMContext):
    await message.answer(globals.WELCOME_TEXT)
    user_telegram_id = message.from_user.id
    site_url = f"https://free-project-3.onrender.com/auto-login/{user_telegram_id}/"
    user_detail = UserDetail.objects.filter(telegram_id=message.from_user.id).first()

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

    # Login band emasligini tekshirish
    if User.objects.filter(username=username).exists():
        await message.answer("Ushbu login band! Iltimos, boshqa login kiriting:")
        return

    await state.update_data(username=username)
    await state.set_state(LoginStates.password)
    await message.answer("Saytga kirish uchun **Parol** o'ylab toping va kiriting:")


@main_router.message(LoginStates.password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    if len(password) < 4:
        await message.answer("Parol juda qisqa! Kamida 4 ta belgidan iborat parol kiriting:")
        return

    data = await state.get_data()
    telegram_id = message.from_user.id
    username_input = data.get('username')

    try:
        # 1. Telegram ID bo'yicha profilni olamiz yoki yaratamiz
        user_detail, created = UserDetail.objects.get_or_create(telegram_id=telegram_id)

        # 2. Agar profilga telegram_user bog'langan bo'lsa, o'sha user'ni yangilaymiz
        if user_detail.telegram_user is not None:
            user = user_detail.telegram_user
            user.username = username_input
            user.set_password(password)
            user.first_name = data.get('first_name', '')
            user.last_name = data.get('last_name', '')
            user.save()
        else:
            # 3. Agar telegram_user bor bo'lmasa (None bo'lsa), username mavjudligini tekshiramiz
            existing_user = User.objects.filter(username=username_input).first()

            if existing_user:
                # Username mavjud bo'lsa, parolini yangilab ushbu user'ni telegram_user ga biriktiramiz
                user = existing_user
                user.set_password(password)
                user.first_name = data.get('first_name', '')
                user.last_name = data.get('last_name', '')
                user.save()
            else:
                # Username yo'q bo'lsa, yangi User yaratamiz
                user = User.objects.create_user(
                    username=username_input,
                    password=password,
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', '')
                )

            # User'ni telegram_user ga biriktiramiz
            user_detail.telegram_user = user

        # 4. Profil ma'lumotlarini saqlaymiz
        user_detail.first_name = data.get('first_name')
        user_detail.last_name = data.get('last_name')
        user_detail.phone_number = data.get('phone_number')
        user_detail.save()

        await state.clear()
        site_url = f"https://free-project-3.onrender.com/auto-login/{telegram_id}/"
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
            f"🔑 **Loginingiz:** `{username_input}`\n"
            f"🔒 **Parolingiz:** `{password}`\n\n"
            f"Endi ushbu ma'lumotlar bilan saytga kirishingiz mumkin.",
            reply_markup=buttons,
            parse_mode="Markdown"
        )

    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        await message.answer("❌ Saqlashda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
