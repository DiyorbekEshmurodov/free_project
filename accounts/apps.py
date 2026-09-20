import os
import sys
import logging
import threading
import asyncio
import subprocess
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Render'da yoki RUN_MAIN bo'lganda botni ishga tushirish
        if os.environ.get('RENDER') or os.environ.get('RUN_MAIN') == 'true' or os.environ.get('SERVER_SOFTWARE'):
            thread = threading.Thread(target=self.run_bot_thread, daemon=True)
            thread.start()

    def run_bot_thread(self):
        # Lokal uchun Ngrok
        if os.environ.get('RUN_MAIN') == 'true' and not os.environ.get('RENDER'):
            def start_ngrok():
                subprocess.Popen(
                    ["ngrok", "http", "8000"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            threading.Thread(target=start_ngrok, daemon=True).start()

        # Botni ishga tushirish va xatolikni konsolga chiqarish
        try:
            print("--- TELEGRAM BOT ISHGA TUSHMOQDA ---", flush=True)
            from run_bot import main
            asyncio.run(main())
        except Exception as e:
            print(f"--- BOTDA XATOLIK BO'LDI: {e} ---", file=sys.stderr, flush=True)