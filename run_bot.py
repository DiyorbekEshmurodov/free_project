import asyncio
from aiogram import Bot, Dispatcher
from django.conf import settings
from apps.bot.bot_main import main_router


async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    # Webhook va kutilayotgan xabarlarni tozalash
    await bot.delete_webhook(drop_pending_updates=True)

    # Routerni biriktirish
    dp.include_router(main_router)

    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot,handle_signals=False)


if __name__ == "__main__":
    # Faqat terminalda 'python run_bot.py' qilingandagina Django setup bo'ladi
    import os
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    asyncio.run(main())