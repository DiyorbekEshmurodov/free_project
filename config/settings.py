"""
Django settings for config project.
"""

from pathlib import Path
import os
import sys
import dotenv
from decouple import config
import dj_database_url
from groq import Groq

BASE_DIR = Path(__file__).resolve().parent.parent

# Apps papkasini importlar uchun qo'shish
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# .env faylini yuklash
dotenv.load_dotenv(BASE_DIR / '.env')

# SECRET_KEY `.env` faylidan olinadi (agar bo'lmasa fallback ishlatiladi)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-b2+c^s#d3jq5y2eg6u!%e-z12wo4_*hcfkhjgfqfgm-&b$b1u#')

# Debug rejimini tekshirish
DEBUG = config('DEBUG', default=False, cast=bool)

# Groq API Sozlamasi
GROQ_API_KEY = config("GROQ_API_KEY", default=None)
groq_client = None
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Hostlar ro'yxati
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost,zippy-upon-unscathed.ngrok-free.dev'
).split(',')


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_ngrok',

    'apps.accounts',
    'apps.ai_app',
    'apps.bot',
    'apps.fitness_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'fitness_app.context_processors.user_profile_status',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database sozlamasi
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    }
else:
    # Standart PostgreSQL sozlamasi (agar DATABASE_URL berilmagan bo'lsa)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='gym_db'),
            'USER': config('DB_USER', default='gym_admin'),
            'PASSWORD': config('DB_PASSWORD', default='root'),
            'HOST': config('DB_HOST', default='127.0.0.1'),
            'PORT': config('DB_PORT', default='5432'),
            'OPTIONS': {
                'client_encoding': 'UTF8'
            }
        }
    }

# Test muhiti uchun tezkor SQLite
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'uz-uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True


# Static va Media fayllar
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Xavfsizlik va Cookie sozlamalari
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Production (HTTPS) uchun True qilinadi, Local muhitda False
CSRF_COOKIE_SECURE = config('SECURE_SSL', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SECURE_SSL', default=False, cast=bool)

CSRF_TRUSTED_ORIGINS = [
    'https://zippy-upon-unscathed.ngrok-free.dev',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]

LOGIN_URL = 'login_page'
BOT_TOKEN = config('BOT_TOKEN', default='dummy-bot-token-for-ci')