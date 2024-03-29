import asyncio
import random
import time
import traceback

import aiohttp
import requests
from fake_useragent import UserAgent
from requests.exceptions import *

from etc.app import bot
from utils.exceptions import *

temp = []


class ParserBase:
    __NBA_validate_min_1q = 0  # 1 quater
    __NBA_validate_sec_1q = 30

    __NBA_validate_min_2q = 5  # 2 quater
    __NBA_validate_sec_2q = 30

    __NBA_validate_min_3q = 10  # 3 quater
    __NBA_validate_sec_3q = 30

    __NBA_validate_min_4q = 15  # 3 quater
    __NBA_validate_sec_4q = 30

    # any liga name in basketball sport, but not "NBA 2K23"
    __NOT_NBA_validate_min_1q = 4  # 1 quater
    __NOT_NBA_validate_sec_1q = 59

    __NOT_NBA_validate_min_2q = 14  # 2 quater
    __NOT_NBA_validate_sec_2q = 59

    __NOT_NBA_validate_min_3q = 24  # 3 quater
    __NOT_NBA_validate_sec_3q = 59

    __NOT_NBA_validate_min_4q = 34  # 4 quater
    __NOT_NBA_validate_sec_4q = 59

    def __init__(self, user_id: str | int = None):
        super().__init__()
        self.__user_id = user_id

    async def valide_timer(self,
                           liga_name: str,
                           quater: int,
                           special_liga: str,
                           max_period: int = 4):
        """
        Используйте этот метод когда в подборе игр нужны параметры.

        :param liga_name: Укажите лигу

        :param special_liga: Укажите специальную лигу

        :param quater: Укажите текущую четверть матча

        :param max_period: Укажите максимальный, возможный период

        :return: Возвращает список с минимальным временем для подбора игр в текущей
            четверти

        """

        if liga_name.count(special_liga):
            validate_minutes = 0
            validate_seconds = 0
            if quater == 1:
                validate_seconds = self.__NBA_validate_sec_1q
                validate_minutes = self.__NBA_validate_min_1q
            elif quater == 2:
                validate_seconds = self.__NBA_validate_sec_2q
                validate_minutes = self.__NBA_validate_min_2q
            elif quater == 3:
                validate_seconds = self.__NBA_validate_sec_3q
                validate_minutes = self.__NBA_validate_min_3q
            elif quater == 4:
                validate_seconds = self.__NBA_validate_sec_4q
                validate_minutes = self.__NBA_validate_min_4q

            return [validate_minutes, validate_seconds]

        else:
            validate_minutes = 0  # минуты
            validate_seconds = 0  # секунды
            if quater == 1:
                validate_seconds = self.__NOT_NBA_validate_sec_1q
                validate_minutes = self.__NOT_NBA_validate_min_1q
            elif quater == 2:
                validate_seconds = self.__NOT_NBA_validate_sec_2q
                validate_minutes = self.__NOT_NBA_validate_min_2q
            elif quater == 3:
                validate_seconds = self.__NOT_NBA_validate_sec_3q
                validate_minutes = self.__NOT_NBA_validate_min_3q
            elif quater == 4:
                validate_seconds = self.__NOT_NBA_validate_sec_4q
                validate_minutes = self.__NOT_NBA_validate_min_4q

            return [validate_minutes, validate_seconds]

    async def get_data_match(self,
                             url: str,
                             filtering: str,
                             mdp: int,
                             retry: int = 5,
                             timeout=2,
                             proxy=None):
        """
        Используйте этот метод, чтобы получить информацию о матче

        :param url: Указывайте ссылку на матч, на ресурс line55w.com, для получения
            информации о нем.

        :param timeout: Устанавливается таймаут, чтобы долго не ждать ответа от
            сервера, а пропускать сборку данных этого url

        :param mdp: Укажите максимальный возможный период у матча, для
            корректной работы метода

        :param filtering: С каким фильтром матч был найден?

        :param retry: Количество повторных попыток подключения

        :return: Возвращает словарь с информацией о матче
        """

        global temp

        data_match = {}
        add_keys = ['scores', 'prognoses']

        for key in add_keys:
            data_match[key] = {}

        try:
            headers = {
                "Accept": "*/*",
                "UserAgent": UserAgent().random
            }

            response = requests.get(url,
                                    headers=headers,
                                    timeout=timeout,
                                    proxies=proxy).json()

            if not response["events"]:
                return

            liveEvent = response["liveEventInfos"]
            scores = response["liveEventInfos"][0]["scores"]

            try:
                data_match["team1"] = response["events"][0]["team1"]
                data_match["team2"] = response["events"][0]["team2"]
            except (IndexError, KeyError):
                pass

            try:
                data_match["part"] = len(liveEvent[0]["scores"][1])
            except IndexError:
                data_match["part"] = 1

            try:
                data_match["timer"] = liveEvent[0]["timer"]
            except (KeyError, ValueError):
                data_match["timer"] = '00:00'

            try:
                data_match["liga"] = response["sports"][1]["name"]
            except (KeyError, ValueError):
                data_match["liga"] = None

            data_match["filter"] = filtering
            event_id = response["events"][0]["id"]
            data_match["event_id"] = event_id
            data_match["json_url"] = url
            data_match["prognoses"] = {}

            for i in range(1, mdp + 1):
                data_match["scores"][f"t1_p{i}"] = 'x'
                data_match["scores"][f"t2_p{i}"] = 'x'

            try:
                parts = len(liveEvent[0]["scores"][1])
            except IndexError:
                parts = 1

            try:
                data_match["scores"]["t1_p1"] = scores[1][0]["c1"]
                data_match["scores"]["t2_p1"] = scores[1][0]["c2"]
            except (IndexError, KeyError):
                data_match["scores"]["t1_p1"] = scores[0][0]["c1"]
                data_match["scores"]["t2_p1"] = scores[0][0]["c2"]

            if 1 < parts:
                for part in range(0, parts):
                    if part >= mdp:
                        continue
                    data_match["scores"][f"t1_p{part + 1}"] = scores[1][part][
                        "c1"]

                    data_match["scores"][f"t2_p{part + 1}"] = scores[1][part][
                        "c2"]

            data_match["scores"]["t1_p0"] = scores[0][0]["c1"]
            data_match["scores"]["t2_p0"] = scores[0][0]["c2"]

            try:
                for i in [1, 2]:
                    try:
                        add_time = liveEvent[0]["extraEvent"]["score"][f"c{i}"]
                    except (IndexError, KeyError):
                        if parts <= mdp:
                            break
                        add_time = scores[1][parts - 1][f"c{i}"]

                    data_match["scores"][f"t{i}_p{mdp}"] = int(
                        data_match["scores"][f"t{i}_p{mdp}"]) + int(add_time)
            except (IndexError, KeyError, TypeError, ValueError):
                pass

            except Exception:
                await bot.send_message("2027466915",
                                       f"Ошибка с от -> "
                                       f"{traceback.format_exc()}")

            if parts > mdp:
                data_match["part"] = mdp

            return data_match

        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectTimeout,
                TimeoutError,
                requests.exceptions.ConnectionError):
            raise

        except Exception:
            if retry:
                await asyncio.sleep(10)
                return self.get_data_match(url=url,
                                           filtering=filtering,
                                           mdp=mdp,
                                           retry=retry - 1)
            else:
                raise ConnectionError

        finally:
            await asyncio.sleep(1)

    async def __last_check_match(self,
                                 event_id: int | str,
                                 filtering: str,
                                 max_period: int = 4,
                                 time_param: bool | str = False,
                                 retry: int = 5,
                                 timeout=2):
        """
        Метод Last_check предназначен для последней проверки на валидность
        ссылки. Исходя из стратегии он должен проверить номер текущего
        периода, чтобы потом узнать, есть ли смысл брать именно эту игру на
        отслеживание

         :param event_id: Идентификатор матча - обязательный параметр,
            требуется для формирования ссылки.

        :param filtering: С каким фильтром был найден матч?

        :param max_period: Укажите максимальный период, для фильтрации матчей

        :param timeout: Устанавливается таймаут, чтобы долго не ждать ответа от
            сервера, а пропускать сборку данных этого url

        """

        url = (f'https://line55w.bk6bba-resources.com/events/event?lang=ru'
               f'&eventId={event_id}&scopeMarket=1600&version=0')

        headers = {"Accept": "*/*",
                   "UserAgent": UserAgent().random}

        try:
            timeout = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout,
                                             headers=headers) as session:
                r = await session.get(url)
                response = await r.json()

            try:
                quater = len(response["liveEventInfos"][0]["scores"][1])
            except (IndexError, KeyError):
                quater = 1

            try:
                response["events"][0]["id"]
                response["sports"][1]["name"]

                try:
                    time_list = response[
                        "liveEventInfos"][0]["timer"].split(':')
                    minutes = int(time_list[0])
                    seconds = int(time_list[1])
                except Exception:
                    minutes = 0
                    seconds = 0

                if quater <= max_period:

                    if time_param:
                        param_minutes = int(time_param.split(':')[0])
                        param_seconds = int(time_param.split(':')[1])
                        if minutes <= param_minutes and seconds < param_seconds:
                            return [url, filtering]

                    else:
                        return [url, filtering]

            except (IndexError, ValueError, KeyError):
                pass

        except TimeoutError:
            pass

        except requests.exceptions.ConnectTimeout:
            await asyncio.sleep(1)

        except Exception:
            if retry:
                await asyncio.sleep(5)
                return await self.__last_check_match(event_id=event_id,
                                                     filtering=filtering,
                                                     max_period=max_period,
                                                     retry=retry - 1)
            else:
                raise NotImplementedError

        finally:
            await asyncio.sleep(1)

    async def __collecting_events_id(self,
                                     sport: str,
                                     user_id: str | int,
                                     filter_leagues: dict,
                                     limit: str | int = 2,
                                     only_leagues: bool = False,
                                     only_sports: bool = False,
                                     retry: int = 10,
                                     timeout=2) -> list:
        """
        Этот метод предназначен для сборки всех идентификаторов матчей по
        фильтрам. Используйте его в том случае если вам нужно получить event
        id матчей по фильтрам

        :param sport: Укажите вид спорта.

        :param only_leagues: Укажите True, только если вам нужно собрать
            названия все лиг в конкретном спорте

        :param filter_leagues: Укажите словарь с ключами blacklist - чтобы
            убрать ненужные лиги из поиска, и searching - какую лигу вы хотите
            найти. Если поиск игр в конкретной лиге является не обязательным
            параметром, то укажите пустую строку

        :param limit: Укажите лимит возвращаемых event_id, по умолчанию лимит
            равен двум

        :param only_sports: Укажите True если вам нужно получить только
            название, и id видов спорта

        :param user_id: Telegram User Id

        :param timeout: Устанавливается таймаут, чтобы долго не ждать ответа от
            сервера, а пропускать сборку данных этого url

        :return: Возвращает список с собранными event_id
            (идентификаторами матча)
        """

        url = 'https://line55w.bk6bba-resources.com/events/list?' \
              'lang=ru&version=0&scopeMarket=1600'

        sport_id_lst = []
        event_id_lst = []
        headers = {"Accept": "*/*",
                   "UserAgent": UserAgent().random}

        try:
            response = requests.get(url, headers=headers,
                                    timeout=timeout).json()

        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout):
            raise requests.exceptions.ConnectTimeout

        except TimeoutError:
            if retry:
                return await self.__collecting_events_id(
                    sport=sport,
                    user_id=user_id,
                    filter_leagues=filter_leagues,
                    limit=limit,
                    only_sports=only_sports,
                    retry=retry - 1
                )
            else:
                raise

        except Exception:
            if retry:
                await asyncio.sleep(10)
                return await self.__collecting_events_id(
                    sport=sport,
                    filter_leagues=filter_leagues,
                    limit=limit,
                    user_id=user_id,
                    only_leagues=only_leagues,
                    only_sports=only_sports,
                    retry=retry - 1
                )
            else:
                raise

        else:

            for response_sport in response["sports"]:
                sport_name = response_sport.get("name")
                sport_id = response_sport.get("id")

                for liga in filter_leagues["searching"]:

                    if sport_name.count(sport) and sport_name.count(liga) \
                            and [sport_id, liga] not in sport_id_lst:

                        if liga == "":
                            if len(filter_leagues["searching"]) > 1:
                                if filter_leagues["searching"][0] != '':
                                    await bot.send_message(user_id,
                                                           'Неправильные '
                                                           'фильтра')

                                for spec_liga in filter_leagues[
                                                     "searching"][1:]:
                                    if not sport_name.count(spec_liga):
                                        sport_id_lst.append([sport_id, liga])

                            elif not sport_name.count('NBA 2K23'):
                                sport_id_lst.append([sport_id, liga])

                        else:
                            sport_id_lst.append([sport_id, liga])

                    if filter_leagues["blacklist"]:
                        try:
                            for black_liga in filter_leagues["blacklist"]:
                                if sport_name.lower().count(black_liga.lower()):
                                    sport_id_lst.remove([sport_id, liga])
                        except ValueError:
                            pass

            for response_events in response["events"]:
                team1 = response_events.get('team1')
                place = response_events.get('place')
                sport_id_event = response_events.get('sportId')

                for sportId in sport_id_lst:
                    if team1 and place == 'live' and sport_id_event == sportId[
                        0] and [sportId[1],
                                response_events.get('id')] not in event_id_lst:
                        event_id_lst.append(
                            [sportId[1], response_events.get('id')])

        if filter_leagues.get("black_id"):
            for black_id in filter_leagues["black_id"]:
                for event_id in event_id_lst:
                    if int(black_id) == int(event_id[1]):
                        event_id_lst.remove(event_id)

        random.shuffle(event_id_lst)
        check = []
        check_id = []
        temp_lst = []

        match limit:
            case 'all':
                for filtering, event_id in event_id_lst:
                    if event_id not in check_id:
                        check.append(filtering)
                        check_id.append(event_id)
                        temp_lst.append([filtering, event_id])

                return temp_lst

            case _:

                for filtering, event_id in event_id_lst:

                    if event_id not in check_id and check.count(
                            filtering) < limit:
                        check.append(filtering)
                        check_id.append(event_id)
                        temp_lst.append([filtering, event_id])

        if not temp_lst:
            raise MatchesNotFoundError

        return temp_lst

    async def get_urls(self,
                       sport: str,
                       user_id: str | int,
                       filter_leagues: dict = None,
                       max_period: int = 4,
                       limit: int | str = 'all',
                       only_leagues: bool = False,
                       only_sports: bool = False,
                       retry: int = 5,
                       time_param: bool | str = False,
                       timeout: int = 3):
        """
        Этот метод предназначен для получения ссылок на отслеживание подходящих
        матчей с максимальной скоростью.

        :param sport: Укажите вид спорта.

        :param filter_leagues: Укажите словарь с фильтрами лиг. Значения в ключе
            blacklist убирают лиги из поиска. Значения в ключе searching - ищут
            конкретную(е) лигу(и). По умолчанию фильтры не заданы

        :param user_id: Telegram User Id

        :param only_leagues: Укажите True, если вам нужно получить только
            название, и id лиг в конкретном спорте.

        :param retry: Количество попыток при ошибке

        :param only_sports: Укажите True если вам нужно получить только
            название, и id видов спорта

        :param limit: Укажите лимит возвращаемых event_id, по умолчанию лимит
            равен двум

        :param max_period: Укажите максимальную четверть матчей, для фильтрации

        :param timeout: Устанавливается таймаут, чтобы долго не ждать ответа от
            сервера, а пропускать сборку данных этого url

        :param time_param: Нужно ли подбирать игры по параметрам времени?
            Если нужно, то укажите список, где по нулевому индексу максимальное
            количество минут, а по первому индексу максимальное
            количество секунд
        """

        if filter_leagues is None:
            filter_leagues = {"searching": [""], "blacklist": []}

        match filter_leagues:
            case {"searching": [*_], "blacklist": [*_]}:
                pass
            case _:
                raise NotImplementedError(
                    "Переданы неправильные ключи в словаре с"
                    "фильтрами")

        tasks = []
        liga_info = []
        tmp = []
        temp_for_name = []

        try:
            for filtering, event_id in await self.__collecting_events_id(
                    sport=sport,
                    user_id=user_id,
                    filter_leagues=filter_leagues,
                    limit=limit,
                    only_leagues=only_leagues,
                    only_sports=only_sports,
                    timeout=timeout):

                if only_leagues or only_sports:
                    liga_info.append([filtering, event_id])

                elif not only_leagues and not only_sports:
                    task = asyncio.create_task(
                        self.__last_check_match(event_id=event_id,
                                                filtering=filtering,
                                                max_period=max_period,
                                                time_param=time_param,
                                                timeout=timeout)
                    )

                    tasks.append(task)

            if only_leagues or only_sports:
                for leagues in liga_info:
                    if leagues[1] not in temp_for_name:
                        temp_for_name.append(leagues[1])
                        tmp.append(leagues)

                return tmp

            urls = await asyncio.gather(*tasks)
            return list(filter(None, urls))

        except (TypeError, IndexError, ValueError):
            pass

        except MatchesNotFoundError:
            pass

        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError):
            pass

        except Exception:
            if retry:
                await asyncio.sleep(5)
                return await self.get_urls(sport=sport,
                                           user_id=user_id,
                                           filter_leagues=filter_leagues,
                                           max_period=max_period,
                                           limit=limit,
                                           only_leagues=only_leagues,
                                           only_sports=only_sports,
                                           retry=retry - 1)
            else:
                raise


def read_file():
    lst = []
    with open('/test-parser.txt') as file:
        rows = file.read().split('Тест')
        for row in rows:
            if row.split(' № ') != ['']:
                num = row.split(' № ')[1].split(', ')[0]
                lst.append(num)

    try:
        num = lst[-1]
    except IndexError:
        num = 0

    return num


async def tests():
    num = read_file()
    start = time.time()
    tmp = []
    p = ParserBase(111)

    """Параметры теста"""
    num = int(num) + 1
    write_file = True
    test_level = "HARD"
    filter_leagues = {"searching": ["", "NBA 2K23"], "blacklist": ["liga-2"],
                      "black_id": ["40006169", "39977378"]}
    time_param = '17:59'
    max_period = 3
    limit = "all"
    sport = 'Баскетбол. '
    parser_type = 'синхронный'
    params = (
        f'Фильтра: {filter_leagues}, Макс. Таймер: {time_param}, макс. период: '
        f'{max_period}, лимит: {limit}, спорт: {sport}')

    matches = await p.get_urls(sport, 111, filter_leagues,
                               time_param=time_param,
                               max_period=max_period, limit=limit)
    for match in matches:
        tmp.append(match)

    finish = round(time.time() - start, 2)
    if write_file:
        with open('test-parser.txt', 'a') as file:
            file.write(
                f'Тест № {num}, [{test_level}]. За {finish} секунд, было собранно '
                f'{len(tmp)} матчей. Был применен {parser_type} парсер.\nПараметры '
                f'теста - {params}\n')

    print(f'Получено {len(tmp)} за {finish} секунд')


async def test_search_and_scanning():
    p = ParserBase(111)
    start = time.time()
    tmp = []

    """Параметры теста"""
    num = int(read_file()) + 1
    write_file = True
    test_level = "CONTROL_TEST SEARCH AND SCAN. LITE"
    filter_leagues = {"searching": ["", "NBA 2K23"], "blacklist": ["ОРО"],
                      "black_id": ["40007587", "40007472"]}
    time_param = False  # '20:59'
    max_period = 4
    limit = 1
    sport = 'Баскетбол. '
    cycle = 20
    params = (
        f'Фильтра: {filter_leagues}, Макс. Таймер: {time_param}, макс. период: '
        f'{max_period}, лимит: {limit}, спорт: {sport}, циклов: {cycle}')
    parser_type = 'совместимый'

    urls = await p.get_urls(sport, 111, filter_leagues, time_param=time_param,
                            max_period=max_period, limit=limit)

    if not urls or len(urls) < (limit * len(filter_leagues["searching"])):
        return await test_search_and_scanning()

    while len(tmp) < cycle:
        for url, filtering in urls:
            start_scan = time.time()
            try:
                scores = await p.get_data_match(url=url, filtering=filtering,
                                                mdp=max_period)
            except:
                await asyncio.sleep(0.5)
                continue
            else:
                finish_scan = round(time.time() - start_scan - 1, 2)
                print(f'{scores}\nПолучено за {finish_scan} секунд')
        tmp.append(1)

    finish = round(time.time() - start, 2)

    if write_file:
        with open('test-parser.txt', 'a') as file:
            file.write(
                f'Тест № {num}, [{test_level}]. За {finish} секунд, было пройдено '
                f'{cycle} циклов. Был применен {parser_type} парсер. Последний матч получил за\n'
                f'{finish_scan} секунд\nПараметры '
                f'теста - {params}\n')

    print(f'Получено {len(urls)} за {finish} секунд')


async def test():
    p = ParserBase()
    url = 'https://line55w.bk6bba-resources.com/events/event?lang=ru&eventId=40829959&scopeMarket=1600&version=0'
    filtering = 'NBA 2K23'
    proxies = []
    with open('../../proxies.txt') as f:
        for row in f.readlines():
            row = row.split('\n')[0]
            method = row.split('://')[0]
            proxy = row
            proxies.append({method: proxy})

    # for proxy in proxies:
    proxy = {
        'http': 'http://31.186.241.8:8888',
    }
    print(proxy)
