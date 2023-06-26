import asyncio
import json
import traceback
from typing import Collection

import requests
from aiogram import Bot

from app.telegram_bot.markups import inline
from core.parsers.parser import ParserBase
from core.types.matches import Match
from core.types.user import Worker
from utils.exceptions import *


async def search_matches(bot: Bot,
                         filter_leagues: dict = None):
    worker = Worker(bot.id)

    if not filter_leagues:
        filter_leagues = await worker.get('filters')

    while await worker.get_scanning_status:
        parser = ParserBase()
        strategy = await worker.strategy
        urls_limit = strategy.urls_limit

        try:

            if len(await worker.urls.get()) < urls_limit:
                urls = await parser.get_urls(sport='Баскетбол. ',
                                             user_id=await worker.user_id,
                                             filter_leagues=filter_leagues,
                                             max_period=strategy.max_part,
                                             time_param=strategy.max_time,
                                             limit=1)
                for url, filtering in urls:
                    if len(await worker.urls.get()) >= urls_limit:
                        break

                    for url_user, filtering_user in await worker.urls.get():
                        if url != url_user and filtering != filtering_user:
                            await worker.urls.append(url=[url, filtering])

                    if not await worker.urls.get():
                        await worker.urls.append(url=[url, filtering])

        except TypeError:
            pass

        finally:
            await asyncio.sleep(3)
            await online_scanner(worker=worker, bot=bot)


async def online_scanner(worker: Worker, bot: Bot):
    parser = ParserBase()
    for url, filtering in await worker.urls.get():

        try:
            data = await parser.get_data_match(
                url=url, filtering=filtering,
                mdp=4, timeout=3
            )

            event_id = url.split("eventId=")[1].split("&")[0]
            match_id = f'{await worker.user_id}|{worker.id}|{event_id}'
            match = Match(match_id)

            if not data:
                await check_bet(
                    match=match,
                    worker=worker,
                    bot=bot
                )

                await worker.urls.delete(url=[url, filtering])
                await match.delete()
                raise MatchFinishError

            data["scores"] = json.dumps(data["scores"])

            if not await match.in_database:
                logger.debug('Создается матч ')
                await create_match(
                    match=match,
                    worker=worker,
                    bot=bot,
                    data=data,
                    url=url
                )

            else:
                if 4 >= data["part"] > await match.part:
                    logger.debug('Обновилась четверть. ')
                    await check_bet(
                        match=match,
                        worker=worker,
                        bot=bot
                    )

                await match.update(data)

            await asyncio.sleep(2)

        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError):
            await asyncio.sleep(5)

        except TypeError:
            print(traceback.format_exc())

        except NotFoundError:
            try:
                await worker.urls.delete(url=[url, filtering])
            except (IndexError, ValueError, KeyError):
                pass

        except MatchFinishError:
            filters = await worker.what_search

            try:
                filters["black_id"].append(event_id)
            except UnboundLocalError:
                pass

            return await search_matches(
                filter_leagues=filters,
                bot=bot
            )

        except Exception:
            print(traceback.format_exc())
            await asyncio.sleep(3)


async def check_bet(bot: Bot,
                    match: Match,
                    worker: Worker,
                    sep: str = '$'):
    strategy = await worker.strategy
    bet_result = await strategy.bet_result(match)

    logger.debug(f'Результат проверенной {await match.part} '
                 f'четверти - {bet_result}')
    if (await match.bets.get_bet(await match.part)).lower().count('пропускаю'):
        return

    type_coincidence = 'guess'
    if not bet_result:
        type_coincidence = 'not_guess'

    try:
        counter = await strategy.update_counter(
            type_coincidence=type_coincidence,
            filtering=await match.filter,
            id=worker.id
        )

    except UninterestingMatch:
        logger.debug('Матч стал не интересным')
        url = await match.json_url
        filtering = await match.filter

        await worker.urls.delete(url=[url, filtering])
        await match.delete()

        raise MatchFinishError

    if not counter:
        return

    if await worker.is_validate_counter(
            type_coincidence=type_coincidence,
            filtering=await match.filter
    ) and counter:

        await send_event(worker=worker,
                         match=match,
                         bot=bot,
                         counter=counter,
                         type_coincidence=type_coincidence,
                         sep=sep)

    elif counter > 1:
        await send_event(worker=worker,
                         counter=counter,
                         match=match,
                         bot=bot,
                         type_coincidence=type_coincidence,
                         sep=sep)


async def send_event(worker: Worker,
                     match: Match,
                     type_coincidence: str,
                     counter: int,
                     bot: Bot,
                     sep: str = '$'):
    strategy = await worker.strategy
    event = await strategy.template_event(
        match_id=match.id,
        type_coincidence=type_coincidence,
        counter=counter,
        sep=sep
    )

    if await match.part >= 4:
        await worker.tmp.events.set_event(
            message=event, filtering=await match.filter
        )

    else:
        bet_on = (f'матч <b>{await match.teams}</b> '
                  f'{await match.bets.get_bet(0)}')

        if await match.part < 3:
            bet_on = (f'{await match.part + 1} четверть '
                      f'<b>{await match.teams}</b> '
                      f'{await match.bets.get_bet(await match.part + 1)}')

        event = '\n'.join(event.split(sep)[:-1])
        text = f"{event}\nПрогноз на {bet_on}"

        await bot.send_message(await worker.chat, text)


def get_bet_message(data: Collection | dict,
                    strategy: str,
                    match_id: str):
    """
    Формирует текст сообщения перед созданием матча
    """
    button = None
    teams = f"<b>{data['team1']} - {data['team2']}</b>"
    logger.debug(f'Стратегия - {strategy}, '
                 f'Четверть - {data["part"]}, '
                 f'Время - {data["timer"]}, '
                 f'Прогнозы - {data["prognoses"]}')

    if strategy.count('random'):
        bet_now = data['prognoses'][f"part{data['part']}"]
        prognos = (f'Прогноз на {data["part"]} четверть '
                   f'{teams} <b>{bet_now}</b>')

        if data['part'] > 3:
            bet_now = data['prognoses'][f"part0"]
            prognos = f'Прогноз на матч {teams} - {bet_now}'

        if bet_now.lower().count('пропускаю'):
            bet_now = data['prognoses'][f"part{data['part'] + 1}"]
            prognos = (f'Прогноз на {data["part"] + 1} четверть '
                       f'{teams} <b>{bet_now}</b>')
            if data["part"] + 1 == 4:
                bet_now = data['prognoses'][f"part0"]
                prognos = f'Прогноз на матч {teams} - {bet_now}'

    else:
        button = inline.check_button(match_id)
        bet_now = ', '.join(data["prognoses"].values())
        prognos = f"Выбранный сценарий для {teams} - ({bet_now})"

    return prognos, button


async def create_match(bot: Bot,
                       match: Match,
                       worker: Worker,
                       data: dict,
                       url: str):
    parser = ParserBase(user_id=await worker.user_id)
    strategy = await worker.strategy
    filtering = data["filter"]

    validate_timer = await parser.valide_timer(
        liga_name=data["liga"],
        quater=data["part"],
        special_liga='NBA 2K23'
    )

    prognos_now_quater = (
            int(validate_timer[0]) >=
            int(data["timer"].split(':')[0])
            and int(validate_timer[1]) >=
            int(data["timer"].split(':')[1])
    )

    if (data["part"] == 4 and prognos_now_quater is False
            and strategy.name.count('random')):
        await worker.urls.delete(url=[url, filtering])
        raise MatchFinishError

    bets = strategy.gen_bets(part=data["part"],
                             prognos_now_quater=prognos_now_quater)

    for bet, part in zip(bets,
                         range(strategy.part_start, len(bets) + 1)):
        data["prognoses"][f"part{part}"] = bet

    try:
        events = await worker.tmp.events.get_event(filtering=filtering)
        for event in events:
            sep = strategy.sep
            event_text = '\n'.join(event.split(sep)[:-1])
            match_id = event.split(sep)[-1].split('%')[0]
            type_coincidence = event.split(sep)[-1].split('%')[1]

            message_attrs = get_bet_message(
                data=data,
                strategy=strategy.name,
                match_id=match_id
            )

            message_finished = f"{event_text}\n{message_attrs[0]}"
            logger.debug(f'Сообщение сформировано - {message_finished}')

            if await worker.is_validate_counter(
                    type_coincidence=type_coincidence,
                    filtering=filtering
            ):
                send = await worker.chat

            else:
                send = await worker.user_id

            await bot.send_message(send, message_finished,
                                   reply_markup=message_attrs[1])

        await worker.tmp.events.delete_event(filtering=filtering)

    except Exception:
        print(traceback.format_exc())

    data["prognoses"] = json.dumps(data["prognoses"])
    await match.create(data)
