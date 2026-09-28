FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Xavfsizlik uchun ildiz bo'lmagan (non-root) appuser foydalanuvchisini yaratish
RUN adduser --disabled-password --gecos "" appuser

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Fayllarni boshqarish huquqini appuser'ga o'tkazish
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Gunicorn WSGI serverini 3 ta worker bilan ishga tushirish
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]