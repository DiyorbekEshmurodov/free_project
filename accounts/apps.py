import os
import threading
import asyncio
import subprocess
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # 1. Kompyuteringizda ishga tushganda (python manage.py runserver)
        if os.environ.get('RUN_MAIN') == 'true':
            self.start_background_tasks(run_ngrok=True)

        # 2. Render serverida ishga tushganda (Gunicorn orqali)
        elif os.environ.get('SERVER_SOFTWARE') or os.environ.get('RENDER'):
            self.start_background_tasks(run_ngrok=False)

    def start_background_tasks(self, run_ngrok=False):
        from run_bot import main

        # Ngrok faqat kompyuteringizda lokal ishlatganda yonadi
        if run_ngrok:
            def start_ngrok():
                subprocess.Popen(
                    ["ngrok", "http", "8000"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            threading.Thread(target=start_ngrok, daemon=True).start()

        # Telegram bot kompyuterda ham, Render'da ham ishlaydi
        def start_bot():
            try:
                asyncio.run(main())
            except Exception as e:
                print(f"Botda xatolik: {e}")

        threading.Thread(target=start_bot, daemon=True).start()