FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Xavfsizlik uchun ildiz bo'lmagan (non-root) appuser foydalanuvchisini yaratish
RUN adduser --disabled-password --gecos "" appuser

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Docker volume'lar ulanadigan papkalar OLDINDAN yaratilib appuser'ga beriladi.
# Aks holda volume root egaligida yaratiladi va collectstatic ruxsat xatosi beradi.
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# gthread: bitta sekin AI so'rovi butun workerni bloklamasin (3 worker x 4 oqim)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--worker-class", "gthread", "--threads", "4", "--timeout", "40", "config.wsgi:application"]
