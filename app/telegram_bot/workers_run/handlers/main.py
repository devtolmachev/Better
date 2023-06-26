import json

from aiogram import Dispatcher, Bot
from aiogram.filters import Text
from aiogram.types import Message

from app.telegram_bot.workers_run.markups.reply import get_worker_markup
from core.schemas.online_scanners.basketball import search_matches
from utils.functions import whose_worker
from utils.repositories import WorkerRepository


async def session_info(msg: Message, bot: Bot):
    worker = WorkerRepository().get(id=bot.id)
    counter = await worker.counter

    def make_human_readable(data: dict[str, list]):
        return [
            "Все другие лиги" if x == ''
            else "Кибер Баскет"
            if x == 'NBA 2K23'
            else x
            for x in data["searching"]
        ]

    count_matches = len(await worker.matches())
    founding_match = await worker.what_search

    counters = await counter.get_counters()

    guessing_info = json.dumps(
        counters,
        ensure_ascii=False,
        indent=3,
        sort_keys=True
    )
    leagues = f"({', '.join(make_human_readable(founding_match))})"
    await bot.send_message(
        chat_id=msg.from_user.id,
        text=f'<b>Угадывания: \n{guessing_info}</b>\n\n'
             f'Сейчас я сканирую {count_matches} матчей\n\n'
             '%s' % (
                 f'Ищу матч в лигах {leagues}'
                 if founding_match is not None
                 else ''
             )
    )


async def what_you_do(msg: Message, bot: Bot):
    worker = WorkerRepository().get(id=bot.id)
    matches = await worker.matches()
    counter = len((await worker.what_search)["searching"])

    if not matches:
        text = "Я в поиске"
        await bot.send_message(
            chat_id=msg.from_user.id,
            text=text
        )

    else:
        strategy = await worker.strategy
        for match_id in matches:
            text = await strategy.template_msg_from_db(match_id=match_id)

            await bot.send_message(
                chat_id=msg.from_user.id,
                text=text
            )


async def register_handlers(
        dp: Dispatcher,
        bot: Bot,
        events_users: bool = False,
        restart_worker: bool = True
):
    dp.message.register(session_info,
                        Text(contains='сессия', ignore_case=True))

    dp.message.register(what_you_do,
                        Text(contains='делаешь', ignore_case=True))

    if events_users is True:
        user = await whose_worker(worker_id=bot.id)
        kb = get_worker_markup().as_markup()
        kb.resize_keyboard = True
        await bot.send_message(
            chat_id=user.id,
            text=f'Я начал свою работу',
            reply_markup=kb
        )
        worker = WorkerRepository().get(id=bot.id)

        if restart_worker is True:
            await worker.reset_worker()

        await search_matches(bot=bot)
