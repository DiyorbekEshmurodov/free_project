import os
import sys
import threading
import asyncio
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        if os.environ.get('RENDER') or os.environ.get('RUN_MAIN') == 'true' or os.environ.get('SERVER_SOFTWARE'):
            thread = threading.Thread(target=self.run_bot_thread, daemon=True)
            thread.start()

    def run_bot_thread(self):
        # Alohida thread uchun event loop yaratish
        try:
            print("--- TELEGRAM BOT ISHGA TUSHMOQDA ---", flush=True)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            from run_bot import main
            loop.run_until_complete(main())
        except Exception as e:
            print(f"--- BOTDA XATOLIK BO'LDI: {e} ---", file=sys.stderr, flush=True)