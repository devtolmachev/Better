import asyncio
import multiprocessing
from multiprocessing import Process
from multiprocessing import Queue
from threading import Thread

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from aiohttp import web, web_request

from app.telegram_bot.workers_run.handlers.main import register_handlers
from core.types.user import Worker
from etc.app import app
from etc.app import webhook_url
from utils.middleware import UtilsMiddleware
from utils.repositories import UserRepository, WorkerRepository
from utils.threads import ThreadAsync

async_util = ThreadAsync()


def webhook_path(token: str):
    return f'/bots/{token}'


@async_util.async_thread
async def start_up_telebot(token: str,
                           dp: Dispatcher,
                           bot: Bot,
                           stop: bool = False,
                           restart_worker: bool = True,
                           queue=None):

    if await Worker(id=bot.id).get_scanning_status is True or stop is True:
        await Worker(id=bot.id).set_scanning_status(False)
        await bot.delete_webhook(drop_pending_updates=True)
        raise OSError

    else:
        worker = Worker(id=bot.id)
        await worker.set_scanning_status(True)
        dp.update.middleware(UtilsMiddleware(bot=bot, dp=dp))

        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(
            url=webhook_url + webhook_path(token=token),
            drop_pending_updates=True
        )

        await register_handlers(
            dp=dp,
            bot=bot,
            events_users=True,
            restart_worker=restart_worker
        )


async def webhook(request: web_request.Request):
    token: str = request.match_info["token"]

    worker = WorkerRepository().get(id=token.split(':')[0])
    if await worker.get_scanning_status is False:
        return

    bot = Bot(token, parse_mode='HTML')
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    request_data = await request.json()
    try:
        user_id = request_data["message"]["from"]["id"]
    except KeyError:
        user_id = request_data["my_chat_member"]["from"]["id"]

    if token in await UserRepository().get(id=user_id).get_workers():
        update = Update(**request_data)

        dp.message.middleware(UtilsMiddleware(bot=bot, dp=dp))
        await register_handlers(dp=dp, bot=bot)
        await dp.feed_update(bot=bot, update=update)

        await bot.session.close()
        return web.Response()

    else:
        return web.Response(status=505)


app.router.add_post('/bots/{token}', webhook)


async def start_workers_user(queue: Queue,
                             workers: list,
                             stop: bool = False,
                             restart_worker: bool = True):
    for worker_token in workers:

        id_worker = worker_token.split(':')[0]

        worker = Worker(id=id_worker)
        if await worker.get('scanning') is True and stop is False:
            await worker.set_scanning_status(False)

        process = Process(
            target=start_up_telebot,
            kwargs={"token": worker_token,
                    'stop': stop,
                    'queue': queue,
                    'restart_worker': restart_worker},
            name=worker_token
        )
        process.start()


def start_workers(queue: Queue,
                  stop: bool,
                  workers: list,
                  restart_worker: bool):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_workers_user(
        queue=queue,
        stop=stop,
        restart_worker=restart_worker,
        workers=workers
    ))


processes: dict[str, Process] = {}


async def start_user_process(id: str | int,
                             queue: Queue,
                             stop: bool = False,
                             restart_worker: bool = True,
                             custom_workers: list[str] | None = None):
    user = UserRepository().get(id=id)
    username = await user.username
    name_process = f"process of {username}"

    if custom_workers is None:
        workers = await UserRepository().get(id=id).get_workers()
    else:

        if not isinstance(custom_workers, list):
            raise NotImplementedError

        workers = custom_workers

    if stop is False:
        process = Process(target=start_workers,
                          kwargs={
                              "queue": queue,
                              "stop": stop,
                              'restart_worker': restart_worker,
                              'workers': workers
                          },
                          name=name_process)
        process.start()
        return "Твои боты заработали"

    else:

        for token in workers:
            kwargs = {
                "token": token,
                "queue": queue,
                "stop": True,
                "restart_worker": False
            }

            pr = Process(
                target=start_up_telebot,
                kwargs=kwargs
            )
            pr.start()
            pr.join()

            pr.kill()

            [
                pr.kill()
                for pr in multiprocessing.active_children()
                if pr.name.count(name_process)
            ]

            return "Твои боты не работают"
