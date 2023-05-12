import asyncio
import traceback

import requests
from aiogram.types import Message

from core.database.crud import QMService
from core.database.main_database import Database
from core.database.repositories import User, Match
from core.parsers.parser import ParserBase
from core.types.matches import Bet
from etc import bot
from source.types.strategies import *
from utils.exceptions import *


async def simple_scanner_fonbet(msg: Message, strategy):
    # My I'd - 2027466915
    user = User(2027466915)
    user.edit('scanning', True)
    user.edit('filters', '{}')
    user.edit('urls', '{}')
    user.edit('strategy', strategy)
    user.edit('tmp_messages', '{}')
    user.edit('info_matches', '{}')

    with Database() as db:
        crud = QMService()
        user.edit(column='counters', value=db.counter_column)
        db.apply_query(crud.truncate(TABLE='matches'))

    await search_matches(msg, strategy)


async def search_matches(msg: Message, strategy: str,
                         filter_leagues: dict = None):
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

    if not filter_leagues:
        filter_leagues = user.get('filters')

    while user.is_scanning:
        parser = ParserBase()
        try:

            if len(user.urls.get()) < urls_limit:
                urls = await parser.get_urls(sport='Баскетбол. ',
                                             user_id=msg.from_user.id,
                                             filter_leagues=filter_leagues,
                                             max_period=strategy.max_part,
                                             time_param=strategy.max_time,
                                             limit=1)
                for url, filtering in urls:

                    if url not in user.urls.get():
                        user.urls.append(url=[url, filtering])

            else:
                await online_scanner(user=user, msg=msg, strategy=strategy,
                                     bot_info=bot_info)

        except TypeError:
            pass

        finally:
            await asyncio.sleep(3)


async def online_scanner(**kwargs):
    user: User = kwargs["user"]
    parser = ParserBase()
    msg: Message = kwargs["msg"]
    strategy: BaseStrategy = kwargs["strategy"]
    bot_info: msg.bot.get_me() = kwargs["bot_info"]

    for url, filtering in user.urls.get():

        try:

            data = await parser.get_data_match(url, filtering=filtering,
                                               mdp=4, timeout=3)
            event_id = url.split("eventId=")[1].split("&")[0]
            match_id = f'{msg.from_user.id}|{bot_info.id}|{event_id}'
            match = Match(match_id)

            if not data:
                await check_bet(match_id=match_id, strategy=strategy,
                                filtering=filtering,
                                url=url, user=user,
                                msg=msg)
                user.urls.delete(url=[url, filtering])
                match.delete()
                raise MatchFinishError

            data["user_id"] = msg.from_user.id
            data["bot_username"] = bot_info.username
            data["scores"] = json.dumps(data["scores"])

            if not match.in_database:
                validate_timer = await parser.valide_timer(
                    liga_name=data["liga"],
                    quater=data["part"],
                    special_liga='NBA 2K23'
                )

                prognos_now_quater = (int(validate_timer[0]) >= int(
                    data["timer"].split(':')[0])
                                      and int(validate_timer[1]) >= int(
                            data["timer"].split(':')[1]
                        )
                                      )

                bets = strategy.gen_bets(part=data["part"],
                                         prognos_now_quater=prognos_now_quater)
                for bet, part in zip(bets, range(strategy.part_start, len(bets) + 1)):
                    data["prognoses"][f"part{part}"] = bet

                try:
                    events = user.tmp_events.get_event(filtering=filtering)
                    for event in events:
                        sep = strategy.sep
                        event = '\n'.join(event.split(sep))
                        teams = f"<b>{data['team1']} - {data['team2']}</b>"

                        bet_now = data['prognoses'][f"part{data['part']}"]
                        prognos = (f'Прогноз на {data["part"]} четверть '
                                   f'{teams} <b>{bet_now}</b>')
                        if data['part'] > 3:
                            prognos = f'Прогноз на матч {teams} - {bet_now}'

                        if strategy.name.lower().count('scenarios'):
                            bet_now = ', '.join(data["prognoses"].values())
                            prognos = (f"Выбранный сценарий для {teams} "
                                       f"- ({bet_now})")

                        message_finished = f"{event}\n{prognos}"
                        await bot.send_message(user.id, message_finished)

                    try:
                        user.tmp_events.delete_event(filtering=filtering)
                    except (IndexError, KeyError):
                        pass

                except Exception:
                    pass

                data["prognoses"] = json.dumps(data["prognoses"])
                match.create(data)

            else:
                if 4 >= data["part"] > match.part:
                    await check_bet(match_id=match_id, strategy=strategy,
                                    filtering=filtering,
                                    url=url, user=user, msg=msg)

                match.update(data)

            await asyncio.sleep(1)

        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout):
            await asyncio.sleep(5)

        except TypeError:
            print(traceback.format_exc())

        except NotFoundError:
            user.urls.delete(url=[url, filtering])

        except MatchFinishError:
            await search_matches(msg, strategy=strategy.name,
                                 filter_leagues=user.what_search)

        except Exception:
            print(traceback.format_exc())
            await asyncio.sleep(3)


async def check_bet(match_id: str, strategy: BaseStrategy,
                    filtering: str, url: str, user: User,
                    msg: Message, sep: str = '$'):
    match = Match(match_id=match_id)

    bet_result = strategy.bet_result(match)
    if isinstance(bet_result, str) and bet_result.count('pass'):
        return

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

    if user.is_validate_counter(type_coincidence=type_coincidence,
                                filtering=filtering) and counter:
        if strategy.name == 'scenarios':
            match
        event = strategy.template_event(user_id=user.id,
                                        match_id=match_id,
                                        filtering=filtering,
                                        type_coincidence=type_coincidence)

        if match.part >= 4:
            user.tmp_events.set_event(message=event, filtering=filtering)

        else:
            bet_on = f'матч <b>{match.teams}</b> {match.bets.get_bet(4)}'
            if match.part < 3:
                bet_on = (f'{match.part + 1} четверть <b>{match.teams}</b> '
                          f'{match.bets.get_bet(match.part + 1)}')

            event = '\n'.join(event.split(sep))
            text = f"{event}\nПрогноз {bet_on}"
            await bot.send_message(msg.from_user.id, text)
