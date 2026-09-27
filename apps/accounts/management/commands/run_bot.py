import asyncio
from django.core.management.base import BaseCommand
from run_bot import main


class Command(BaseCommand):
    help = "Telegram botni alohida xizmat sifatida ishga tushirish"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- TELEGRAM BOT ISHGA TUSHMOQDA ---"))
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Bot to'xtatildi."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"--- BOTDA XATOLIK BO'LDI: {e} ---"))