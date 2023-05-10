from aiogram.types import Message

from core.database.repositories import UserRepository


def security(func):
    async def wrapper(*args, **kwargs):
        msg: Message = args[0]
        UserRepository().save(msg.from_user.id, msg.from_user.username)

        if str(msg.from_user.id) in ['1611383976', "2027466915"]:
            try:
                return await func(*args)
            except Exception:
                return await func(*args, kwargs["state"])
        else:
            await msg.answer('Пошел нахуй отсюда')

    return wrapper
