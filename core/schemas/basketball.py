import asyncio
import traceback

import requests
from aiogram.types import Message

from core.database.crud import CRUDService
from core.database.main_database import Database
from core.database.repositories import User
from core.parsers.parser import ParserBase
from core.types.dynamic import Match, Bet
from etc import bot
from source.types.strategies import *
from utils.exceptions import MatchFinishError, UninterestingMatch


async def simple_scanner_fonbet(msg: Message, strategy):
    # My I'd - 2027466915
    user = User(msg.from_user.id)
    user.edit('scanning', True)
    user.edit('filters', '{}')
    user.edit('urls', '{}')
    user.edit('strategy', strategy)

    with Database() as db:
        crud = CRUDService()
        user.edit(column='counters', value=db.counter_column)
        db.apply_query(crud.truncate('matches'))

    await start_scanner(msg, strategy)


async def start_scanner(msg: Message, strategy: str):
    user = User(msg.from_user.id)
    urls_limit = None

    strategies = [Randomaizer(), Scenarios()]
    for strategy in strategies:
        if strategy.name == user.strategy:
            urls_limit = strategy.urls_limit
            user.edit('strategy', strategy.name)
            user.edit('filters', strategy.filters)
            break

    bot_info = await msg.bot.get_me()

    while user.is_scanning:
        parser = ParserBase()
        try:

            if len(user.urls.get()) < urls_limit:
                for url in await parser.get_urls(sport='Баскетбол. ', user_id=msg.from_user.id,
                                                 filter_leagues=user.get_info('filters'),
                                                 max_period=4, time_param='30:59',
                                                 limit=1):

                    if url not in user.urls.get() and len(user.urls.get()) < urls_limit:
                        user.urls.append(url)
        except TypeError:
            pass

        else:

            for url, filtering in user.urls.get():

                try:

                    data = await parser.get_data_match(url, filtering=filtering, max_period=4, timeout=3)
                    match_id = f'{msg.from_user.id}|{bot_info.id}|{url.split("eventId=")[1].split("&")[0]}'
                    match = Match(match_id)

                    if not data:
                        bet = Bet(match_id=match_id)
                        bet_result = bet.compare_bet_with_score()

                        type_coincidence = 'guess'
                        if not bet_result:
                            type_coincidence = 'not_guess'

                        try:
                            counter = strategy.update_counter(type_coincidence=type_coincidence,
                                                              filtering=filtering, user_id=user.id)

                        except UninterestingMatch:
                            user.urls.delete(url=[url, filtering])
                            match.delete()
                            raise MatchFinishError

                        if user.is_validate_counter(type_coincidence=type_coincidence, filtering=filtering) and counter:
                            if bet_result:
                                await bot.send_message(msg.from_user.id, "У меня зашла ставка ")
                            else:
                                await bot.send_message(msg.from_user.id, "У меня не зашла ставка ")

                        user.urls.delete(url=[url, filtering])
                        match.delete()
                        raise MatchFinishError

                    data["user_id"] = msg.from_user.id
                    data["bot_username"] = bot_info.username
                    data["scores"] = json.dumps(data["scores"])

                    if not match.in_database:
                        validate_timer = await parser.valide_timer(liga_name=data["liga"], quater=data["part"],
                                                                   special_liga='NBA 2K23')
                        prognos_now_quater = (int(validate_timer[0]) >= int(data["timer"].split(':')[0]) and
                                              int(validate_timer[1]) >= int(data["timer"].split(':')[1]))

                        bets = strategy.gen_bets(quater=data["part"],
                                                 prognos_now_quater=prognos_now_quater)
                        for bet, part in zip(bets, range(1, len(bets) + 1)):
                            data["prognoses"][f"part{part}"] = bet

                        data["prognoses"] = json.dumps(data["prognoses"])
                        match.create(data)

                    else:
                        bet = Bet(match_id=match_id)
                        if 4 >= data["part"] > match.part:
                            bet_result = bet.compare_bet_with_score()

                            type_coincidence = 'guess'
                            if not bet_result:
                                type_coincidence = 'not_guess'

                            try:
                                counter = strategy.update_counter(type_coincidence=type_coincidence,
                                                                  filtering=filtering, user_id=user.id)

                            except UninterestingMatch:
                                user.urls.delete(url=[url, filtering])
                                match.delete()
                                raise MatchFinishError

                            if user.is_validate_counter(type_coincidence=type_coincidence, filtering=filtering) \
                                    and counter:
                                bet_msg = "зашла"
                                if not bet_result:
                                    bet_msg = 'не зашла'
                                await bot.send_message(msg.from_user.id, f"У меня {bet_msg} ставка {counter} раз подряд"
                                                                         f"\nСтратегия - {strategy.name}\n"
                                                                         f"Матч - {match.teams}\n")

                        match.update(data)

                    await asyncio.sleep(1)

                except (requests.exceptions.ConnectTimeout, TypeError):
                    print(traceback.format_exc())
                    await asyncio.sleep(5)

                except MatchFinishError:
                    await asyncio.sleep(10)

                except Exception:
                    print(traceback.format_exc())
                    await asyncio.sleep(3)
