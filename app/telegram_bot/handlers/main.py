from aiogram import Dispatcher
from aiogram.types import Message

from app.telegram_bot.decorators import security
from core.schemas import basketball


@security
async def on_startup(msg: Message):
    await basketball.simple_scanner_fonbet(msg, 'random')


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(on_startup)