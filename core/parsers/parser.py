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

    # any liga name in basketball sport, but not "NBA 2K23"
    __NOT_NBA_validate_min_1q = 4  # 1 quater
    __NOT_NBA_validate_sec_1q = 59

    __NOT_NBA_validate_min_2q = 14  # 2 quater
    __NOT_NBA_validate_sec_2q = 59

    __NOT_NBA_validate_min_3q = 24  # 3 quater
    __NOT_NBA_validate_sec_3q = 59

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

        if quater < max_period:
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

                return [validate_minutes, validate_seconds]
        else:
            return [0, 0]

    async def get_data_match(self,
                             url: str,
                             filtering: str,
                             max_period: int,
                             retry: int = 5,
                             timeout=2):
        """
        Используйте этот метод, чтобы получить информацию о матче

        :param url: Указывайте ссылку на матч, на ресурс line55w.com, для получения
            информации о нем.

        :param timeout: Устанавливается таймаут, чтобы долго не ждать ответа от
            сервера, а пропускать сборку данных этого url

        :param max_period: Укажите максимальный возможный период у матча, для
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
            headers = {"Accept": "*/*",
                       "UserAgent": UserAgent().random}

            response = requests.get(url, headers=headers, timeout=timeout).json()

            if not response["events"]:
                raise MatchFinishError

            try:
                data_match["team1"] = response["events"][0]["team1"]
                data_match["team2"] = response["events"][0]["team2"]
            except (IndexError, KeyError):
                pass

            try:
                data_match["part"] = len(response["liveEventInfos"][0]["scores"][1])
            except IndexError:
                data_match["part"] = 1

            try:
                data_match["timer"] = response["liveEventInfos"][0]["timer"]
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

            for i in range(1, max_period + 1):
                data_match["scores"][f"t1_p{i}"] = 'x'
                data_match["scores"][f"t2_p{i}"] = 'x'

            try:
                parts = len(response["liveEventInfos"][0]["scores"][1])
            except IndexError:
                parts = 1

            try:
                data_match["scores"]["t1_p1"] = \
                    response["liveEventInfos"][0]["scores"][1][0]["c1"]
                data_match["scores"]["t2_p1"] = \
                    response["liveEventInfos"][0]["scores"][1][0]["c2"]
            except (IndexError, KeyError):
                data_match["scores"]["t1_p1"] = \
                    response["liveEventInfos"][0]["scores"][0][0]["c1"]
                data_match["scores"]["t2_p1"] = \
                    response["liveEventInfos"][0]["scores"][0][0]["c2"]

            if 1 < parts <= 4:
                for part in range(1, parts + 1):
                    data_match["scores"][f"t1_p{part}"] = \
                        response["liveEventInfos"][0]["scores"][1][part - 1]["c1"]

                    data_match["scores"][f"t2_p{part}"] = \
                        response["liveEventInfos"][0]["scores"][1][part - 1]["c2"]

            data_match["scores"]["t1_p0"] = \
                response["liveEventInfos"][0]["scores"][0][0]["c1"]
            data_match["scores"]["t2_p0"] = \
                response["liveEventInfos"][0]["scores"][0][0]["c2"]

            try:
                for i in [1, 2]:
                    add_time = response["liveEventInfos"][0]["scores"][1][parts - 1][f"c{i}"]
                    data_match[f"t{i}_p{max_period}"] = (
                            int(data_match[f"t{i}_p4"]) + int(add_time))

            except (IndexError, KeyError):
                pass

            except Exception:
                logger.critical(f'Произошла ошибка с ОТ -> {traceback.format_exc()}')
                await bot.send_message(self.__user_id, f'Произошла ошибка с ОТ -> '
                                                       f'{traceback.format_exc()}')

            return data_match

        except requests.exceptions.ConnectionError:
            raise

        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectTimeout,
                TimeoutError):

            raise

        except MatchFinishError:
            pass

        except Exception:
            if retry:
                logger.warning(
                    f'Произошла ошибка с url: '
                    f'{url}\nОсталось попыток подключится - {retry}\n'
                    f'{traceback.format_exc()}')
                await asyncio.sleep(10)
                return self.get_data_match(url=url,
                                           filtering=filtering,
                                           max_period=max_period,
                                           retry=retry - 1)
            else:
                raise ConnectionError

        finally:
            await asyncio.sleep(1)

    async def __last_check_match(self,
                                 event_id: int | str,
                                 max_period: int = 5,
                                 time_param: bool | str = False,
                                 retry: int = 5,
                                 timeout=2):
        """
        Метод Last_check предназначен для последней проверки на валидность ссылки.
        Исходя из стратегии он должен проверить номер текущего периода, чтобы потом
        узнать, есть ли смысл брать именно эту игру на отслеживание

         :param event_id: Идентификатор матча - обязательный параметр, требуется для
            формирования ссылки.

        :param max_period: Укажите максимальный период, для фильтрации матчей

        :param timeout: Устанавливается таймаут, чтобы долго не ждать ответа от
            сервера, а пропускать сборку данных этого url

        """

        url = f'https://line55w.bk6bba-resources.com/events/event?lang=ru&eventId=' \
              f'{event_id[1]}&scopeMarket=1600&version=0'

        headers = {"Accept": "*/*",
                   "UserAgent": UserAgent().random}
        logger.debug(f'Запрашиваю данные у сайта -> {url}. Заголовки запроса -> '
                     f'{headers}. Тайм-аут {timeout} секунды')

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
                    time_list = response["liveEventInfos"][0]["timer"].split(':')
                    minutes = int(time_list[0])
                    seconds = int(time_list[1])
                except Exception:
                    minutes = 0
                    seconds = 0

                logger.debug(f'Таймер проверяемого матча -> {minutes}:{seconds}')

                if quater <= max_period:

                    if time_param:
                        param_minutes = int(time_param.split(':')[0])
                        param_seconds = int(time_param.split(':')[1])
                        if minutes <= param_minutes and seconds < param_seconds:
                            logger.debug('Матч прошел проверку по времени')
                            return [url, event_id[0]]
                        else:
                            logger.debug('Матч не прошел проверку по времени')

                    else:
                        logger.debug('Возвращаю url')
                        return [url, event_id[0]]

                else:
                    logger.debug(f'Игра не подошла по параметрам периода')

            except (IndexError, ValueError, KeyError):
                logger.debug(
                    f'Не удалось структурировать информацию о матче. Скорее всего '
                    f'матч закончился')

        except TimeoutError:
            pass

        except requests.exceptions.ConnectTimeout:
            await asyncio.sleep(1)

        except Exception:
            if retry:
                logger.error(
                    f'Произошла ошибка с url: {url}\nОсталось попыток подключится - '
                    f'{retry}\n\n'
                    f'{traceback.format_exc()}')
                await asyncio.sleep(5)
                return await self.__last_check_match(event_id=event_id,
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
        Этот метод предназначен для сборки всех идентификаторов матчей по фильтрам.
        Используйте его в том случае если вам нужно получить event id матчей по
        фильтрам

        :param sport: Укажите вид спорта.

        :param only_leagues: Укажите True, только если вам нужно собрать названия
            все лиг в конкретном спорте

        :param filter_leagues: Укажите словарь с ключами blacklist - чтобы убрать
            ненужные лиги из поиска, и searching - какую лигу вы хотите найти. Если
            поиск игр в конкретной лиге является не обязательным параметром, то
            укажите пустую строку

        :param limit: Укажите лимит возвращаемых event_id, по умолчанию лимит равен
            двум

        :param only_sports: Укажите True если вам нужно получить только название, и
            id видов спорта

        :param user_id: Telegram User Id

        :param timeout: Устанавливается таймаут, чтобы долго не ждать ответа от
            сервера, а пропускать сборку данных этого url

        :return: Возвращает список с собранными event_id (идентификаторами матча)
        """

        url = 'https://line55w.bk6bba-resources.com/events/list?' \
              'lang=ru&version=0&scopeMarket=1600'

        sport_id_lst = []
        event_id_lst = []
        headers = {"Accept": "*/*",
                   "UserAgent": UserAgent().random}

        try:
            logger.debug(
                f'Посылаю запрос на -> {url}. Заголовки запроса -> {headers}')
            response = requests.get(url, headers=headers, timeout=timeout).json()

        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError):
            raise requests.exceptions.ConnectTimeout

        except TimeoutError:
            if retry:
                return await self.__collecting_events_id(sport=sport,
                                                         user_id=user_id,
                                                         filter_leagues=filter_leagues,
                                                         limit=limit,
                                                         only_sports=only_sports,
                                                         retry=retry - 1)
            else:
                raise

        except Exception:
            logger.critical(f'{traceback.format_exc()}')
            if retry:
                await asyncio.sleep(10)
                return await self.__collecting_events_id(sport=sport,
                                                         filter_leagues=filter_leagues,
                                                         limit=limit,
                                                         user_id=user_id,
                                                         only_leagues=only_leagues,
                                                         only_sports=only_sports,
                                                         retry=retry - 1)
            else:
                raise

        else:

            logger.debug(f'Беру эти фильтры -> {filter_leagues}')

            for response_sport in response["sports"]:
                sport_name = response_sport.get("name")
                sport_id = response_sport.get("id")

                for liga in filter_leagues["searching"]:

                    if sport_name.count(sport) and sport_name.count(liga) \
                            and [sport_id, liga]    not in sport_id_lst:

                        if liga == "":
                            if len(filter_leagues["searching"]) > 1 and \
                                    filter_leagues["searching"][0] == "":
                                for sports in sport_id_lst:
                                    if "" not in sports:
                                        sport_id_lst.append([sport_id, liga])

                                for spec_liga in filter_leagues["searching"][:1]:
                                    if spec_liga not in sport_name:
                                        sport_id_lst.append([sport_id, liga])
                            else:
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
                    if team1 and place == 'live' and sport_id_event == sportId[0] \
                            and [sportId[1],
                                 response_events.get('id')] not in event_id_lst:
                        event_id_lst.append([sportId[1], response_events.get('id')])

        logger.debug(f'Необработанные лиги - {sport_id_lst}')
        logger.debug(f'Id матчей до перемешки - {event_id_lst}')

        if filter_leagues.get("black_id"):
            for black_id in filter_leagues["black_id"]:
                for event_id in event_id_lst:
                    if int(black_id) in event_id:
                        event_id_lst.remove(event_id)

        random.shuffle(event_id_lst)
        logger.debug(f'Id матчей после перемешки - {event_id_lst}')
        logger.debug(f'Лимит игр в лиге -> {limit}')
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

                    if event_id not in check_id and check.count(filtering) < limit:
                        check.append(filtering)
                        check_id.append(event_id)
                        temp_lst.append([filtering, event_id])

        if len(temp_lst) < len(filter_leagues["searching"]):
            raise MatchesNotFoundError

        logger.debug(
            f'Возвращаю отфильтрованные идентификаторы матчей -> {temp_lst}')
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

        :param only_leagues: Укажите True, если вам нужно получить только название, и
            id лиг в конкретном спорте.

        :param retry: Количество попыток при ошибке

        :param only_sports: Укажите True если вам нужно получить только название,
            и id видов спорта

        :param limit: Укажите лимит возвращаемых event_id, по умолчанию лимит равен
            двум

        :param max_period: Укажите максимальную четверть матчей, для фильтрации

        :param timeout: Устанавливается таймаут, чтобы долго не ждать ответа от
            сервера, а пропускать сборку данных этого url

        :param time_param: Нужно ли подбирать игры по параметрам времени? Если нужно,
            то укажите список, где по нулевому индексу максимальное количество минут,
            а по первому индексу максимальное количество секунд
        """

        if filter_leagues is None:
            filter_leagues = {"searching": [""], "blacklist": []}

        match filter_leagues:
            case {"searching": [*_], "blacklist": [*_]}:
                pass
            case _:
                raise NotImplementedError("Переданы неправильные ключи в словаре с"
                                          "фильтрами")

        tasks = []
        liga_info = []
        tmp = []
        temp_for_name = []

        try:
            for event_id in await self.__collecting_events_id(sport,
                                                              user_id,
                                                              filter_leagues,
                                                              limit=limit,
                                                              only_leagues=only_leagues,
                                                              only_sports=only_sports,
                                                              timeout=timeout):
                try:

                    if only_leagues or only_sports:
                        liga_info.append(event_id[1])

                    elif not only_leagues and not only_sports:
                        if time_param:
                            validate_time = f"{time_param.split(':')[0]} - " \
                                            f"{time_param.split(':')[1]}"
                            logger.debug(
                                f'Параметры времени включены. Текущее время матча '
                                f'должно быть не более {validate_time}')

                        elif not time_param:
                            logger.debug(
                                f'Параметры времени отключены -> {time_param}')

                        logger.debug(
                            f'Максимальный период который может быть у матча -> '
                            f'{max_period}')

                        task = asyncio.create_task(self.__last_check_match(event_id,
                                                                           max_period,
                                                                           time_param,
                                                                           timeout=timeout))

                        tasks.append(task)

                except Exception:
                    continue

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
                logger.critical(f'Ошибка в методе get_urls. Делаю еще '
                                f'попытку. Осталось {retry} попыток\n\n'
                                f'{traceback.format_exc()} ')
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
    with open('/home/daniil/PycharmProjects/better/test-parser.txt') as file:
        rows = file.read().split('Тест')
        for row in rows:
            if row.split(' № ') != ['']:
                num = row.split(' № ')[1].split(', ')[0]
                lst.append(num)

    num = lst[-1]
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

    matches = await p.get_urls(sport, 111, filter_leagues, time_param=time_param,
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
                                                max_period=max_period)
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


if __name__ == '__main__':
    asyncio.run(test_search_and_scanning())
