import json
import random
import time
import traceback

from aiogram.filters import Text
from aiogram.filters.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery,
                           Message,
                           InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.telegram_bot.handlers.main import manage_profile
from app.telegram_bot.markups import inline
from app.telegram_bot.markups.pagination import Pagination
from core.strategies import Strategies
from core.types.user import Worker
from etc import dp, bot
from utils.functions import check_worker
from utils.repositories import WorkerRepository, UserRepository


class Widgets(StatesGroup):
    first = State()


class WorkersManage(StatesGroup):
    change_token = State()


@dp.callback_query(Text(contains='_liga:'))
async def change_pagination(call: CallbackQuery, worker_id: str | int):
    worker = WorkerRepository().get(id=worker_id)

    strategy = await worker.strategy
    counter = await worker.counter

    liga = call.data.split(':')[-1].split('_')[0]
    action = call.data.split(':')[0].split('_')[0]

    name_strategy = strategy.name

    if call.data.count('$') == 2:
        value = call.data.split('$value_counter_')[1].split('$')[0]
        await counter.change_max_counter(
            bookmaker=await worker.bookmaker,
            strategy=strategy.name,
            sport=await worker.sport,
            liga="" if liga.count("all") else liga,
            value=value
        )

        builder = InlineKeyboardBuilder(
            markup=call.message.reply_markup.inline_keyboard[:-1]
        )

        await call.answer("Счетчик изменен!", show_alert=True)

    else:

        await call.answer()
        kb = Pagination().change_step(
            action, call.message.reply_markup,
            'choice_counter_liga:'
            f'{liga}_{worker_id}'
        )

        builder = InlineKeyboardBuilder(markup=kb.inline_keyboard)

    builder.row(
        *inline.Navigation().back_button(
            'counters',
            call_=f"change_counter_{name_strategy}_{worker_id}",
            text="Вернуться"
        )
    )

    reply_markup = builder.as_markup().inline_keyboard.copy()
    if reply_markup[0][0].text.lower().count('настройки'):
        reply_markup.pop(0)

    counters = await counter.get_max_counter(
        bookmaker=await worker.bookmaker,
        sport=await worker.sport,
        strategy=strategy.name
    )

    max_counter = counters["" if liga.count('all') else liga]

    reply_markup.insert(0, [InlineKeyboardButton(
        callback_data="show_liga:%s_%s" % (liga, worker_id),
        text=f"Настройки - {max_counter}"
    )])

    kb = InlineKeyboardBuilder(markup=reply_markup)
    text = "Все остальные лиги" if liga.count('all') else liga
    text = (f"Бот @{await worker.username}\nЛига - <b>{text}</b>\n"
            f"Стратегия - <b>{strategy.Name}</b>")

    await bot.edit_message_text(chat_id=call.from_user.id,
                                message_id=call.message.message_id,
                                text=text,
                                reply_markup=kb.as_markup())


@dp.callback_query(Text(contains='list_workers', ignore_case=True))
async def back_to_menu(call: CallbackQuery):
    await call.answer()
    msg = Message(
        message_id=call.message.message_id,
        chat=call.message.chat,
        date=time.time(),
        from_user=call.from_user
    )

    await manage_profile(msg, method='EDIT')


@dp.callback_query(Text(contains='back', ignore_case=True))
async def back_to(call: CallbackQuery, worker_id: str | int):
    await call.answer()
    if call.data.count("settings"):
        await manage_worker_settings(call=call, worker_id=worker_id)

    elif call.data.count("to_worker"):
        await menu_worker(call=call, worker_id=worker_id)


@dp.callback_query(Text(contains='change_bookmaker'))
async def change_bookmaker(call: CallbackQuery, worker_id: str | int):
    await call.answer()
    text = "На данный момент это все поддерживаемые букмекеры."

    kb = InlineKeyboardBuilder()
    bookmakers = ['Fonbet/Pari']
    for bookmaker in bookmakers:
        text_button = bookmaker
        btn = InlineKeyboardButton(
            text=text_button,
            callback_data=f'bookmakers_menu_{bookmaker.lower()}'
        )
        kb.add(btn)

    btn = inline.Navigation().back_button(
        to="settings",
        call_=f'back_worker_settings_{worker_id}'
    )
    kb.row(*btn)

    await bot.edit_message_text(chat_id=call.from_user.id,
                                message_id=call.message.message_id,
                                text=text, reply_markup=kb.as_markup())


@dp.callback_query(Text(contains='worker_change_strategy'))
async def change_strategy(call: CallbackQuery, worker_id: str | int):
    await call.answer()
    utils_buttons = inline.Navigation()
    worker = Worker(id=worker_id)
    strategies = Strategies().get_all()
    worker_strategy = await worker.strategy

    text = f'Все стратегии на данный момент.'

    kb = InlineKeyboardBuilder()
    kb.as_markup(row_width=2)
    [kb.add(
        InlineKeyboardButton(
            **{
                'callback_data':
                    f"worker_strategy_{strategy.name}_{worker_id}",

                'text':
                    (strategy.Name
                     if not worker_strategy.name.count(strategy.name)
                     else f"✅ ({strategy.Name})"
                     )
            })
    )
        for strategy in strategies]

    [
        kb.row(btn)
        for btn in [utils_buttons.back_button('worker', call=call)]
    ]

    await bot.edit_message_text(chat_id=call.from_user.id, text=text,
                                reply_markup=kb.as_markup(),
                                message_id=call.message.message_id)


@dp.callback_query(Text(contains='worker_strategy'))
async def see_info_about_strategy(call: CallbackQuery):
    await call.answer()
    buttons: list[
        InlineKeyboardButton
    ] = [
        btn
        for row in call.message.reply_markup.inline_keyboard
        for btn in row
        if not btn.text.lower().count('назад')
    ]

    util_button = inline.Navigation()
    text = f'Все стратегии на данный момент.'

    kb = util_button.edit_success_btn(btns=buttons, call=call)

    if all([not x.text.lower().count('применить')
            for row in kb.export()
            for x in row]):
        kb.add(util_button.apply_button('strategy', call=call))

    kb.adjust(2)
    reply_markup = kb.as_markup()
    new_buttons_list = reply_markup.inline_keyboard

    if all([
        not x.text.count('✅')
        for row in new_buttons_list
        for x in row
        if not x.text.lower().count('применить')
    ]):
        [
            new_buttons_list[
                new_buttons_list.index(row)
            ].remove(btn)

            for row in new_buttons_list
            for btn in row
            if btn.text.lower().count('применить')
        ]

    reply_markup.inline_keyboard.append(
        [util_button.back_button('worker', call=call)]
    )

    await bot.edit_message_text(chat_id=call.from_user.id, text=text,
                                reply_markup=reply_markup,
                                message_id=call.message.message_id)


@dp.callback_query(Text(contains='worker_delete', ignore_case=True))
async def delete_worker(call: CallbackQuery, state: FSMContext,
                        worker_id: str | int):
    await call.answer()
    utils_btns = inline.Navigation()

    if call.data.count('_yes_'):
        d = await state.get_data()
        attempts = 1 if not d.get("attempts") else d["attempts"] + 1
        await state.update_data(attempts=attempts)

        if attempts == 3:
            worker = Worker(id=call.data.split('_')[-1])
            text = f"Бот @{await worker.username} удален"

            await worker.delete()

            kb = InlineKeyboardBuilder()
            kb.add(*utils_btns.back_button('list'))

            kb.adjust(1)
            await bot.edit_message_text(chat_id=call.from_user.id,
                                        message_id=call.message.message_id,
                                        text=text,
                                        reply_markup=kb.as_markup())
            await state.clear()
            return

    elif call.data.count('_no_'):
        call.Config.allow_mutation = True
        call.message.Config.allow_mutation = True
        msg = call.message
        msg.from_user.id = call.from_user.id
        await state.clear()

        return await manage_profile(msg=msg, method='edit')

    text = 'Ты уверен что хочешь удалить своего бота?'
    yes = ['Да, уверен', "Уверен!", "На 100 % уверен"]
    no = ["Дай-ка мне подумать", 'Не уверен', "Я не буду его удалять!"]
    variables = [random.choice(no), random.choice(yes), random.choice(no)]
    random.shuffle(variables)
    kb = InlineKeyboardBuilder()

    def wrc(yes_: bool = True):
        """Worker Return Callback"""
        word = 'yes' if yes_ is True else 'no'
        return f"worker_delete_{word}_{worker_id}"

    btns = [
        InlineKeyboardButton(
            text=variables[0],
            callback_data=wrc(False) if variables[0].lower().count(
                'не'
            ) else wrc()),

        InlineKeyboardButton(
            text=variables[1],
            callback_data=wrc(False) if variables[1].lower().count(
                'не'
            ) else wrc()),

        InlineKeyboardButton(
            text=variables[2],
            callback_data=wrc(False) if variables[2].lower().count(
                'не'
            ) else wrc())]

    [kb.add(btn) for btn in btns]
    kb.adjust(1)
    await bot.edit_message_text(chat_id=call.from_user.id,
                                message_id=call.message.message_id,
                                text=text,
                                reply_markup=kb.as_markup())


@dp.callback_query(Text(contains='apply_changes'))
async def apply_settings_changes(call: CallbackQuery, worker_id: str | int):
    buttons: list[InlineKeyboardButton] = [
        btn
        for row in call.message.reply_markup.inline_keyboard
        for btn in row
    ]

    if call.data.count('strategy'):
        for btn in buttons:
            if not btn.text.count('✅'):
                continue

            strategy_name = btn.text.split('(')[1].split(')')[0].lower()
            strategy = Strategies().get_strategy_by_name(
                name_strategy=strategy_name
            )
            worker = Worker(id=worker_id)
            await worker.edit(columns='strategy', values=strategy.name)
            await worker.edit(columns='filters', values=strategy.filters)

            text = "Настройки успешно изменены ✅"
            await call.answer(text=text, show_alert=True)
            await menu_worker(call=call, worker_id=worker_id)
            break


@dp.callback_query(Text(contains='change_token', ignore_case=True))
async def change_token(call: CallbackQuery, state: FSMContext,
                       worker_id: str | int):
    await call.answer()

    await state.update_data(id_worker=worker_id)

    await state.set_state(WorkersManage.change_token)
    text = "Пришли новый токен"
    await bot.send_message(call.from_user.id, text)


@dp.message(WorkersManage.change_token)
async def set_new_token_worker(msg: Message,
                               state: FSMContext):
    if not msg.text.count(':') and len(msg.text.split(':')) != 2:
        await state.clear()
        await bot.send_message(msg.from_user.id, "Неправильный формат токена")
        return

    id_worker = msg.text.split(':')[0]
    token = msg.text

    try:
        await check_worker(token=token)
    except ValueError:
        await bot.send_message(msg.from_user.id, "Токен не верный!")
    except Exception:
        await bot.send_message(msg.from_user.id, traceback.format_exc())
    else:
        utils_btns = inline.Navigation()

        worker = WorkerRepository().get(id=id_worker)
        user = UserRepository().get(id=msg.from_user.id)

        old_token = await worker.token
        await user.rename_id_worker(old_data=old_token, new_data=token)
        await worker.edit('token', token)

        token = (f"Токен бота @{await worker.username} изменен!\n\n"
                 f"<b>Старый токен</b> \n{old_token}\n\n"
                 f"<b>Новый токен</b> \n{token}")
        kb = InlineKeyboardBuilder()
        kb.add(*utils_btns.back_button('list'))
        await bot.send_message(msg.from_user.id,
                               token,
                               reply_markup=kb.as_markup())

        await state.clear()


@dp.callback_query(Text(contains='liga_counter'))
async def select_value_of_counter(call: CallbackQuery, worker_id: str | int):
    await call.answer()
    worker = WorkerRepository().get(worker_id)
    strategy = await worker.strategy
    counter = await worker.counter

    text = call.message.text
    liga = call.data.split('_')[-2]
    kb = Pagination().create_pagination(
        callback_data=f'choice_counter_liga:{liga}_{worker_id}',
        data=range(1, 81),
        type_pagination='value_counter',
        sep='_'
    )

    name_strategy = strategy.name
    builder = InlineKeyboardBuilder(
        markup=kb.as_markup().inline_keyboard
    )

    builder.row(
        *inline.Navigation().back_button(
            'counters',
            call_=f"change_counter_{name_strategy}_{worker_id}",
            text="Вернуться"
        )
    )

    max_counter = (await counter.get_max_counter(
        bookmaker=await worker.bookmaker,
        strategy=strategy.name,
        sport=await worker.sport,
    ))["" if liga.count('all') else liga]

    reply_markup = kb.as_markup().inline_keyboard.copy()
    reply_markup.insert(0, [InlineKeyboardButton(
        callback_data="show_liga:%s_%s" % (liga, worker_id),
        text=f"Настройки - {max_counter}"
    )])

    kb = InlineKeyboardBuilder(markup=reply_markup)
    kb.row(
        *inline.Navigation().back_button(
            'counters',
            call_=f"change_counter_{name_strategy}_{worker_id}",
            text="Вернуться"
        )
    )

    await bot.edit_message_text(chat_id=call.from_user.id,
                                message_id=call.message.message_id,
                                text=text,
                                reply_markup=kb.as_markup())


@dp.callback_query(Text(contains='change_counter'))
async def change_counters(call: CallbackQuery, worker_id: str | int):
    await call.answer()
    worker = Worker(id=worker_id)
    counter = await worker.counter
    strategy = await worker.strategy

    counters = await counter.get_max_counter(
        strategy=strategy.name,
        bookmaker=await worker.bookmaker,
        sport=await worker.sport
    )

    hum_read_counter = {
        ("Все остальные лиги" if liga == "" else liga): counter
        for liga, counter in counters.items()
    }

    json_counters = json.dumps(
        hum_read_counter,
        ensure_ascii=False,
        indent=4,
        sort_keys=True
    )

    text = (f"Бот @{await worker.username}\nСтратегия - "
            f"{strategy.Name}\n\n"
            f"<b>{json_counters}</b>")

    kb = InlineKeyboardBuilder()

    attrs_btns = [
        {"callback_data": (f"liga_counter_"
                           f"{'all' if liga_nat == '' else liga_nat}"
                           f"_{worker_id}"),
         "text": liga_hr}
        for liga_nat, liga_hr in zip(counters.keys(), hum_read_counter.keys())
    ]

    [kb.add(InlineKeyboardButton(**attrs)) for attrs in attrs_btns]
    kb.adjust(2)

    kb.row(
        *inline.Navigation().back_button(
            to="counters",
            call_=f'worker_manage_settings_{worker.id}'
        )
    )

    await bot.edit_message_text(chat_id=call.from_user.id,
                                message_id=call.message.message_id,
                                text=text,
                                reply_markup=kb.as_markup())


@dp.callback_query(Text(contains='change_sport'))
async def change_sport(call: CallbackQuery):
    await call.answer()
    kb = InlineKeyboardBuilder()


@dp.callback_query(Text(contains='manage_communication', ignore_case=True))
async def manage_communication(call: CallbackQuery, worker_id: str | int):
    await call.answer()
    worker = Worker(id=worker_id)
    kb = InlineKeyboardBuilder()

    if call.data.count('for'):
        if call.data.count('me'):
            text = f'Теперь твои боты будут присылать сообщения тебе'
            await worker.edit(
                columns='communication_chat',
                values=str(call.from_user.id)
            )
        elif call.data.count('chat'):
            text = f'Находится в разработке'

        kb.add(*inline.Navigation().back_button(''))
        await bot.edit_message_text(
            chat_id=call.from_user.id,
            text=text,
            reply_markup=kb.as_markup()
        )
        return

    [
        kb.add(InlineKeyboardButton(
            **{"callback_data": call_data,
               "text": text}
        ))

        for call_data, text in [(f"manage_communication_for_chat_{worker.id}",
                                 "Присылать сообщения в чат"),
                                (f"manage_communication_for_me_{worker.id}",
                                 "Присылать сообщения мне")]
    ]
    kb.adjust(2)
    kb.row(*inline.Navigation().back_button(
        to="settings",
        call_=f'worker_manage_settings_{worker.id}'
    ))

    text = "Это виды коммуникаций с ботами, выбери наиболее удобный"

    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=kb.as_markup()
    )


@dp.callback_query(Text(contains='manage_settings'))
async def manage_worker_settings(call: CallbackQuery, worker_id: str | int):
    await call.answer()
    worker = WorkerRepository().get(worker_id)
    strategy = await worker.strategy

    kb = InlineKeyboardBuilder()
    strategy = strategy.name
    btns_attrs = [
        {"text": "Счетчики",
         "callback_data": f"change_counter_worker_{strategy}_{worker.id}"},

        {'callback_data': f'worker_change_bookmaker_{worker.id}',
         'text': 'Букмекеры'},

        {'callback_data': f'worker_change_sport_{worker.id}',
         'text': 'Виды спорта'},

        {'callback_data': f'worker_manage_communication_{worker.id}',
         'text': 'Коммуникация'},

    ]

    [kb.add(InlineKeyboardButton(**attrs)) for attrs in btns_attrs]
    kb.adjust(2)

    kb.row(inline.Navigation().back_button(call=call))
    reply_markup = kb.as_markup(row_width=2)

    text = "Настройки бота"
    await bot.edit_message_text(chat_id=call.from_user.id,
                                text=text,
                                reply_markup=reply_markup,
                                message_id=call.message.message_id)


@dp.callback_query(Text(contains='live_page'))
async def get_live_worker_page(call: CallbackQuery, worker_id: str):
    await call.answer()
    worker = Worker(id=worker_id)
    btn = inline.Navigation().back_button(
        call=call
    )
    kb = InlineKeyboardBuilder()
    kb.add(btn)

    webhook_info = await bot.get_webhook_info()
    data_scanning = await worker.get_scanning_status

    status = "Сканирует 🟢" if data_scanning else "Не сканирует 🔴"
    try:
        counters = [
            {(
                'Все лиги' if filtering == ''
                else f"Лиги {filtering}"
            ): {
                (
                    'угадал' if type_coincidence == 'guess'
                    else 'не угадал'
                ): f"{counter} раз подряд"}}
            for type_coincidence in ['guess', 'not_guess']
            for filtering in (await worker.filters)["searching"]
            for counter in [await (await worker.counter).get_counter(
                filtering=filtering,
                type_coincidence=type_coincidence,
                bookmaker=await worker.bookmaker,
                sport=await worker.sport
            )]
        ]
        c = []

        for d in counters:
            for liga in d:
                for coincidence in d[liga]:
                    if not c or not any([x.get(liga) for x in c]):
                        c.append(
                            {liga: {
                                coincidence: d[liga][coincidence]
                            }}
                        )
                    else:
                        index = [
                            c.index(d)
                            for d in c
                            for x in d
                            if x == liga
                        ][0]
                        c[index][liga][coincidence] = d[liga][coincidence]

        counters = json.dumps(
            c,
            ensure_ascii=False,
            indent=4,
            sort_keys=True
        )

        if status.lower().startswith('сканирует'):
            text = (
                f"Бот @{await worker.username} {status.lower()}\n\n"
                f"Сканирует {await worker.bookmaker}.\nИщет игры в "
                f"спорте «{await worker.sport}»\n "
                f"{f'Счетчики - <b>{counters}</b>' if counters else ''}"
            )
        else:
            text = f"Бот @{await worker.username} {status.lower()}"

        await bot.edit_message_text(
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=kb.as_markup()
        )

    except KeyError:
        print(traceback.format_exc())
        pass


@dp.callback_query(Text(contains='worker_menu', ignore_case=True))
async def menu_worker(call: CallbackQuery, worker_id: str | int):
    await call.answer()
    worker = Worker(id=worker_id)

    bets = await worker.bets_statistic
    strategy = await worker.strategy

    success_bets = bets["success"]
    failed_bets = bets["failed"]
    strategy = strategy.Name

    text = (f'Помощник @{await worker.username}\n'
            f'Букмекер: {await worker.bookmaker}\n'
            f'Выигранные ставки: {success_bets}\n'
            f'Проигранные ставки: {failed_bets}\n'
            f"Токен бота: {await worker.token}\n"
            f"Стратегия: {strategy}")

    kb = InlineKeyboardBuilder()

    buttons = [
        {"callback_data": f'worker_change_strategy_{worker.id}',
         'text': 'Стратегии'},
        {'callback_data': f'worker_manage_settings_{worker.id}',
         'text': 'Настройка'},
        {'callback_data': f'worker_change_token_{worker.id}',
         'text': 'Изменить токен'},
        {'callback_data': f'worker_live_page_{worker.id}',
         'text': 'Live Страница'},
        {"callback_data": f"worker_delete_{worker.id}",
         "text": "Удалить бота"}
    ]

    [kb.add(InlineKeyboardButton(**d)) for d in buttons]
    kb.adjust(2)

    kb.row(*inline.Navigation().back_button('list'))
    reply_markup = kb.as_markup(row_width=2)

    await call.message.edit_text(text=text, reply_markup=reply_markup)


def see_handlers():
    pass
