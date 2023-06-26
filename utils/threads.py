import asyncio
import traceback
from asyncio import AbstractEventLoop
from multiprocessing import Pipe, Queue
from types import FunctionType

from aiogram import Bot, Dispatcher
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramUnauthorizedError,
    TelegramBadRequest
)

from utils.repositories import WorkerRepository

queue = Queue()

dps: dict[str, Dispatcher] = {}
bots: dict[str, Bot] = {}
loops: dict[str, AbstractEventLoop] = {}


class ThreadAsync:
    __loops = loops
    __dp = dps

    def async_thread(self, func: FunctionType):
        global dps, loops, bots

        def wrapper(*args, **kwargs):
            token: str = kwargs['token']
            q: Queue = kwargs['queue']

            if self.__loops.get(token) is None:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop=loop)
                bot = Bot(token=token, parse_mode='HTML')
                dp = Dispatcher()
                loops[token] = loop
                dps[token] = dp
                bots[token] = bot

            else:
                loop = loops[token]
                dp = dps[token]
                bot = bots[token]

            kwargs['dp'] = dp
            kwargs['bot'] = bot

            if loop.is_running() is False:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(func(*args, **kwargs))
            except OSError:
                loop.run_until_complete(self.shutdown(bot=bot))
                loop.stop()
                loop.close()
                self.__loops.pop(token)
            except (TelegramForbiddenError,
                    TelegramUnauthorizedError,
                    TelegramBadRequest) as exc:

                if (isinstance(exc, TelegramBadRequest) and
                        not exc.message.count("chat not found")):
                    return

                if isinstance(exc, TelegramUnauthorizedError):
                    username = asyncio.run(
                        WorkerRepository().get(token).username)
                    text = f'Проверь токен бота @{username}'

                else:
                    data = loop.run_until_complete(bot.get_me())

                    if isinstance(exc, TelegramForbiddenError):
                        text = f'Ты заблокировал бота @{data.username}'

                    elif isinstance(exc, TelegramBadRequest):
                        text = f"Запусти бота - @{data.username}"

                    else:
                        raise NotImplementedError('Не выявленное исключение!\n'
                                                  f'{exc}\n\n'
                                                  f'{traceback.format_exc()}')

                queue.put(text)

            except Exception:
                print(traceback.format_exc())

        return wrapper

    def close_loop_bot(self, token: str):
        raise OSError

    @staticmethod
    async def shutdown(bot: Bot):
        owner_id = await WorkerRepository().get(
            id=bot.id
        ).user_id
        # await bot.send_message(owner_id,
        #                        "Я заканчиваю свою работу")
        session = bot.session
        await session.close()
