import asyncio
import random
from types import FunctionType

from aiogram.types import Message

from utils.repositories.user import UserRepository


def security(func):
    async def wrapper(*args, **kwargs):
        msg: Message = args[0]
        user = UserRepository().get(id=msg.from_user.id)
        await UserRepository().save(
            id=msg.from_user.id,
            username=msg.from_user.username
        )

        if not await user.register_time:
            await user.set_register_time()

        if str(msg.from_user.id) in ['1611383976', "2027466915"]:
            try:
                return await func(*args, **kwargs)
            except TypeError:
                return await func(*args)
        else:
            await msg.answer('Пошел нахуй отсюда')

    return wrapper


def rename(func: FunctionType):
    def wrapper(*args, **kwargs):
        return wrapper(*args, **kwargs)

    wrapper.__name__ = f"func_№{random.randrange(0, 100000000000)}"
    return wrapper


def async_process(func: FunctionType):

    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(func(*args, *kwargs))

    return wrapper
