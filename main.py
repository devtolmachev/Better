import logging

from aiogram import executor

from app.telegram_bot.handlers.main import register_handlers
from etc import dp


def on_startup():
    register_handlers(dp)
    logging.basicConfig(level=logging.INFO)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup())
