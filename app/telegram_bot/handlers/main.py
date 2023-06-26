import asyncio
import datetime
import json
import traceback

from aiogram import Dispatcher
from aiogram.filters import Text, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (Message,
                           InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.telegram_bot.decorators import security
from app.telegram_bot.markups import reply
from app.telegram_bot.workers_run.startup import start_workers_user, \
    start_user_process
from core.types.user import User
from core.types.user.workers import Worker
from etc import bot, dp
from utils.functions import get_queue_data, check_worker
from utils.repositories.user import UserRepository
from utils.threads import queue


class HireWorkers(StatesGroup):
    set_token = State()
    set_worker = State()
    delete_worker = State()


@security
async def start(msg: Message):
    user = UserRepository().get(id=msg.from_user.id)

    time = datetime.datetime.now().time()
    username = await user.username
    if time.hour >= 18:
        salution = f'Добрый вечер {username}'
    elif time.hour >= 23 or time.hour < 4:
        salution = f'Доброй ночи {username}'
    elif 4 <= time.hour < 12:
        salution = f'Доброго утра {username}'
    else:
        salution = f'Добрый день {username}'

    await bot.send_message(msg.from_user.id, f"{salution}! ",
                           reply_markup=reply.get_start_kb())


@security
class AddWorker:

    @staticmethod
    @dp.callback_query(Text(text='add_worker'))
    @dp.message(Text(contains='Добавить помощника👨👨🏻‍💻'))
    async def hire_worker(msg: Message, state: FSMContext):
        await state.set_state(HireWorkers.set_token)
        await bot.send_message(msg.from_user.id, "Пришли токен")

    @staticmethod
    @dp.message(HireWorkers.set_token)
    async def add_info_about_worker(msg: Message, state: FSMContext):
        TOKEN = msg.text
        user = UserRepository().get(id=msg.from_user.id)

        if TOKEN in await user.get_workers():
            await state.clear()

            kb = InlineKeyboardBuilder()
            btn = InlineKeyboardButton(
                text='Посмотреть бота >>>',
                callback_data=f'worker_menu_{TOKEN.split(":")[0]}'
            )
            kb.add(btn)

            await bot.send_message(msg.from_user.id,
                                   "Бот с таким токеном уже привязан!",
                                   reply_markup=kb.as_markup())
            return

        try:
            response = await check_worker(token=TOKEN)

        except ValueError:
            await bot.send_message(msg.from_user.id, 'Токен неверный!')
        except Exception:
            print(traceback.format_exc())

        else:
            await state.update_data(worker_token=msg.text)
            await state.update_data(worker_id=response["result"]["id"])
            await state.update_data(worker_info=json.dumps({
                'name': response["result"]["first_name"],
                'username': response["result"]["username"]
            }, ensure_ascii=False))

            data = await state.get_data()

            await msg.answer(
                f'Токен {msg.text} привязан\n'
                f'Id бота: {data["worker_id"]}.\n'
                f'Все верно?'
            )
            await state.set_state(HireWorkers.set_worker)

    @staticmethod
    @dp.message(HireWorkers.set_worker)
    async def add_worker(msg: Message, state: FSMContext):

        if msg.text.lower().count('нет'):
            await bot.send_message(chat_id=msg.from_user.id,
                                   text="Окей, добавление бота отменено")
            await state.clear()
            return

        data = await state.get_data()
        data["worker_name"] = msg.text
        await UserRepository().add_worker(
            id=msg.from_user.id,
            worker_id=data["worker_id"],
            token=data["worker_token"],
            worker_info=data["worker_info"]
        )
        await bot.send_message(msg.from_user.id, "Воркер добавлен!")
        await state.clear()


async def stop_workers(msg: Message):
    message = await start_user_process(
        id=msg.from_user.id,
        queue=queue,
        stop=True
    )

    await asyncio.sleep(1)

    for data in get_queue_data():
        await bot.send_message(msg.from_user.id, data)
    else:
        if message:
            await bot.send_message(msg.from_user.id, str(message))


async def start_workers(msg: Message):
    message = await start_user_process(
        id=msg.from_user.id,
        queue=queue
    )

    await asyncio.sleep(1)

    for data in get_queue_data():
        await bot.send_message(msg.from_user.id, data)
    else:
        await bot.send_message(msg.from_user.id, message)


async def get_profile(msg: Message):
    profile_navigate = reply.MyProfileNavigation()
    user = UserRepository().get(id=msg.from_user.id)

    time = datetime.datetime.fromtimestamp(
        int(await user.register_time)
    ).strftime('%d-%m-%Y %H:%M:%S')

    num = 0
    for id_worker in await user.get_workers():
        worker = Worker(id=id_worker)
        num += (await worker.bets_statistic)["success"]

    text = (f'Ник: <b>@{await user.username}</b>\n'
            f'Зарегистрирован в проекте: <b>{time}</b>\n'
            f'У твоих помощников зашли ставки <b>{num}</b> раз\n')
    await bot.send_message(msg.from_user.id, text,
                           reply_markup=profile_navigate.get_options_profile())


async def manage_profile(msg: Message, method: str = 'SEND'):
    user = User(id=msg.chat.id)
    kb = InlineKeyboardBuilder()
    workers = await user.get_workers()
    for id in workers:
        worker = Worker(id=id)
        btn = InlineKeyboardButton(text=f'@{await worker.username}',
                                   callback_data=f'worker_menu_{worker.id}')
        kb.add(btn)

        user = UserRepository().get(id=msg.from_user.id)

    time = datetime.datetime.fromtimestamp(
        int(await user.register_time)
    ).strftime('%d-%m-%Y %H:%M:%S')

    num = 0
    for id_worker in await user.get_workers():
        worker = Worker(id=id_worker)
        num += (await worker.bets_statistic)["success"]

    text = (f'Ник: <b>@{await user.username}</b>\n'
            f'Зарегистрирован в проекте: <b>{time}</b>\n'
            f'У твоих помощников зашли ставки <b>{num}</b> раз\n')

    if not workers:
        new_text = text.split('\n').copy()
        new_text.pop(-2)
        new_text.append("У тебя нет помощников")
        text = '\n'.join(new_text)
        kb.add(InlineKeyboardButton(text='>>> Добавить бота <<<',
                                    callback_data='add_worker'))

    kb.adjust(2)
    reply_markup = kb.as_markup()

    if method.lower().count('send'):
        await bot.send_message(msg.from_user.id, text,
                               reply_markup=reply_markup)

    elif method.lower().count('edit'):
        await msg.edit_text(text, reply_markup=reply_markup)

    else:
        raise NotImplementedError(f'Метода {method} нет в функции')


async def run_all_workers(msg: Message):
    await start_workers_user(id=msg.from_user.id, queue=queue)

    await bot.send_message(
        chat_id=msg.from_user.id,
        text="Ребята работают"
    )

    for text in get_queue_data():
        await bot.send_message(chat_id=msg.from_user.id, text=text)


def register_handlers(_dp_: Dispatcher):
    _dp_.message.register(start, Command('start'))

    _dp_.message.register(run_all_workers, Command('run'))

    _dp_.message.register(start_workers, Command('w'))

    _dp_.message.register(stop_workers, Command('p'))

    _dp_.message.register(manage_profile,
                          Text(
                              contains='Мой профиль',
                              ignore_case=True
                          ))
