from threading import Thread

from aiogram.types import Message

from core.database.repositories import UserRepository


def security(func):
    async def wrapper(*args, **kwargs):
        msg: Message = args[0]
        UserRepository().save(msg.from_user.id, msg.from_user.username)

        if str(msg.from_user.id) in ['1611383976', "2027466915"]:
            return await func(*args)
        else:
            await msg.answer('Пошел нахуй отсюда')

    return wrapper
