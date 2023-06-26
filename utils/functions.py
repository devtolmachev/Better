import traceback
from typing import Any

import aiogram.exceptions
from aiogram import Bot, Dispatcher
from aiohttp import ClientSession
from fake_useragent import UserAgent

from core import Database
from core.types.user import Worker, User
from utils.repositories import (WorkerRepository as WorkerRepository,
                                UserRepository as UserRepository)
from .threads import queue


async def whose_worker(worker_id: str | int | Any) -> UserRepository.get:
    worker = WorkerRepository().get(id=worker_id)
    user_id = await worker.user_id
    return UserRepository().get(id=user_id)


def get_queue_data():
    while not queue.empty():
        yield queue.get()


async def on_shutdown_workers(_dp: Dispatcher, workers_conf: str = 'automatic'):
    for id in await WorkerRepository().get_all():
        worker = Worker(id=id)
        await worker.set_scanning_status(False)
        user = User(str(await worker.user_id))
        send = False

        try:
            bot = Bot(await worker.token)
            dp_worker = Dispatcher()

            try:
                text = "Я заканчиваю свою работу"
                send = True

            except Exception:
                print(traceback.format_exc())

        #     except (ChatNotFound,
        #             BotBlocked):
        #         pass
        #
        # except Unauthorized:
        #     send = True
        #     text = ("Предупреждение! Проверь токены ботов, "
        #             "один из них неправильный!")

        except aiogram.utils.token.TokenValidationError:
            pass

        except Exception:
            print(traceback.format_exc())

        finally:
            try:

                bot = Bot(await worker.token)
                dp_worker = Dispatcher()
                if send is True:
                    await bot.send_message(user.id, text,
                                           disable_notification=True)

                await bot.delete_webhook()
                session = bot.session
                await session.close()

            except aiogram.utils.token.TokenValidationError:
                pass

            except Exception:
                print(traceback.format_exc())


def logs_control():
    ...


async def check_worker(token: str):
    ua = UserAgent().random
    headers = {
        "Accept": "*/*",
        "User-Agent": ua
    }
    async with ClientSession(headers=headers) as session:
        get_bot = await session.get(
            f'https://api.telegram.org/bot{token}/getMe'
        )
        if get_bot.status != 200:
            raise ValueError
        else:
            response = await get_bot.json()
            return response


async def get_worker_id_by_username(username: str) -> Worker:
    query = (
            """SELECT id FROM workers 
        WHERE worker_info->'username' = '"%s"' """ % username
    )
    async with Database() as db:
        worker_id = await db.get_one(query=query)
        return Worker(id=worker_id)
