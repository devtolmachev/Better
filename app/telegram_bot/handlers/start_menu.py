import multiprocessing
import threading

from aiogram.filters import Text
from aiogram.types import (Message,
                           InlineKeyboardButton, CallbackQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.telegram_bot.workers_run.startup import start_user_process
from etc import dp, bot
from utils.repositories import UserRepository, WorkerRepository
from utils.threads import queue


def see_menu_handlers(): ...


@dp.callback_query(Text(contains='start_menu_worker'))
async def get_info_running_worker(call: CallbackQuery, worker_id: str):
    worker = WorkerRepository().get(id=worker_id)
    markup = call.message.reply_markup

    for row in markup.inline_keyboard:
        for btn in row:
            if btn.callback_data == call.data:
                if btn.text.count('🔴'):
                    # Если бот не работает

                    new_symbol = '🟢'
                    kwargs = {
                        'id': call.from_user.id,
                        'queue': queue,
                        'stop': False,
                        'restart_worker': False,
                        'custom_workers': [await worker.token]
                    }
                else:
                    # Если бот работает

                    new_symbol = '🔴'
                    kwargs = {
                        'id': call.from_user.id,
                        'queue': queue,
                        'stop': True,
                        'restart_worker': False,
                        'custom_workers': [await worker.token]
                    }

                text_btn = btn.text.split()
                text_btn.pop(-1)
                text_btn.append(new_symbol)
                btn.text = ' '.join(text_btn)
                await start_user_process(**kwargs)

    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        text=call.message.text,
        reply_markup=markup
    )


@dp.message(Text(contains='меню запуска', ignore_case=True))
async def start_menu(msg: Message):
    kb = InlineKeyboardBuilder()
    user = UserRepository().get(id=msg.from_user.id)
    workers = await user.get_workers()

    [
        kb.add(InlineKeyboardButton(
            text=f"@{await worker.username} %s" %
                 ('🟢' if await worker.get_scanning_status is True
                  else '🔴'),
            callback_data=f"start_menu_worker_{worker_id}"
        ))
        for worker_id in workers
        for worker in [WorkerRepository().get(id=worker_id)]
    ]
    kb.adjust(2)

    text = f"Меню запущенных ботов"

    await bot.send_message(
        chat_id=msg.from_user.id,
        text=text,
        reply_markup=kb.as_markup()
    )
