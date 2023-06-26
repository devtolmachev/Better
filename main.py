from aiogram import Dispatcher
from aiogram.types import Update
from aiohttp import web, web_request

from app.telegram_bot.handlers.main import register_handlers
from app.telegram_bot.handlers.start_menu import see_menu_handlers
from app.telegram_bot.handlers.visual_manage import see_handlers
from core import Database
from etc.app import app, bot, dp
from etc.app import webhook_url
from utils.functions import on_shutdown_workers
from utils.middleware import WorkersCallbackMiddleware

logfile_name = 'debug.log'
webhook_path = '/bot'


async def on_startup():
    async with Database(): ...
    register_handlers(dp)
    see_handlers()
    see_menu_handlers()
    # for user_id in await UserRepository().get_all():
    #     await start_user_process(id=user_id, queue=queue,
    #                              restart_worker=False)
    #
    #     for data in get_queue_data():
    #         await bot.send_message(user_id, data)


async def on_shutdown(_dp: Dispatcher):
    await on_shutdown_workers(_dp=dp)


async def webhook(request: web_request.Request):
    request_data = await request.json()

    update = Update(**request_data)
    await dp.feed_update(bot, update)
    return web.Response()


app.router.add_post(webhook_path, webhook)


async def main(app_: web.Application):
    await on_startup()

    dp.callback_query.middleware.register(WorkersCallbackMiddleware())

    await bot.set_webhook(
        url=webhook_url + webhook_path,
        drop_pending_updates=True
    )


if __name__ == '__main__':
    app.on_startup.append(main)
    app.on_shutdown.append(on_shutdown)
    web.run_app(
        app,
        port=8080,
        host='0.0.0.0'
    )
