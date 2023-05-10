from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import Message

from app.telegram_bot.decorators import security
from app.telegram_bot.markups import reply
from core.database.repositories import UserRepository
from core.schemas import basketball
from core.types.dynamic import Match
from etc import bot
from source.types.strategies import Randomaizer, Scenarios


class StatesUser(StatesGroup):
    choice_strategy = State()


@security
async def select_strategy(msg: Message):
    await bot.send_message(msg.from_user.id, "Выбери стратегию", reply_markup=reply.get_start_kb())
    await StatesUser.choice_strategy.set()


@security
async def start_online_scanner(msg: Message, state: FSMContext):
    strategy = 'random'
    if msg.text.lower().startswith('сценарии'):
        strategy = 'scenarios'
    await state.finish()
    await bot.send_message(msg.from_user.id, 'Сканирование началось!', reply_markup=reply.get_online_scan_kb())
    await basketball.simple_scanner_fonbet(msg=msg, strategy=strategy)


@security
async def load_matches_from_db(msg: Message):
    user = UserRepository().get(user_id=msg.from_user.id)
    for strategy in [Scenarios(), Randomaizer()]:
        if strategy.name == user.strategy:
            if not user.matches():
                await bot.send_message(msg.from_user.id, f'Я в поиске')
            for match_id in user.matches():
                match = Match(match_id=match_id)
                await bot.send_message(msg.from_user.id, strategy.template_checking_message(user.id, match_id))



@security
async def cancel(msg: Message):
    user = UserRepository()
    user.set_scanning(user_id=msg.from_user.id, status=False)
    await bot.send_message(msg.from_user.id, "✅")


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(select_strategy, commands='start')
    dp.register_message_handler(start_online_scanner, state=StatesUser.choice_strategy)
    dp.register_message_handler(load_matches_from_db, Text(contains='что ты делаешь', ignore_case=True))
    dp.register_message_handler(cancel, Text(contains='завершить', ignore_case=True))
