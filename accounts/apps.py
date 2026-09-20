import os
import threading
import asyncio
import subprocess
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Render serverida yoki lokalda botni alohida thread'da yoqish
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('SERVER_SOFTWARE') or os.environ.get('RENDER'):
            thread = threading.Thread(target=self.run_bot_thread, daemon=True)
            thread.start()

    def run_bot_thread(self):
        from run_bot import main

        # Ngrok faqat kompyuteringizda (lokal) ishlatilganda yonadi
        if os.environ.get('RUN_MAIN') == 'true' and not os.environ.get('RENDER'):
            def start_ngrok():
                subprocess.Popen(
                    ["ngrok", "http", "8000"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            threading.Thread(target=start_ngrok, daemon=True).start()

        # Telegram botni ishga tushirish
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Botda xatolik: {e}")