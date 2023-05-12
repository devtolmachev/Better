from typing import Any, Collection

import utils.exceptions
from core.types.matches import Bet, Scores
from core.types.static import BaseType


class Urls(BaseType):
    """
    Управление ссылками пользователей на отслеживание матчей
    """

    def __init__(self, user_id: str | int):
        self.__user_id = user_id

    def append(self, url: list):
        """
        Добавить url в базу
        :param url: Url должен содержать ссылку на отслеживание - и фильтр с
            которым был найден матч
        :type url: list
        """
        query = super()._qm.unite('users', columns='urls', values=url,
                                  user_id=f"= '{self.__user_id}'")
        super()._database.apply_query(query)

    def get(self) -> Collection[list[str, str]]:
        """
        Получить url пользователя
        :return: Возвращает Url сканированных матчей пользователя
        :rtype: list
        """
        query = super()._qm.read('users', columns='urls',
                                 user_id=f"= '{self.__user_id}'")

        result = super()._database.get_one(query=query)
        if not result:
            result = []

        return result

    def delete(self, url: list | str):
        """
        Удалить url пользователя
        :param url: Список со ссылкой на отслеживание
        :type url: list
        """
        query = super()._qm.read('users', columns='urls',
                                 user_id=f"= '{self.__user_id}'")
        urls: list = super()._database.get_one(query=query)
        urls.remove(url)
        if not urls:
            urls = ['[]']
        query_update = super()._qm.update('users',
                                          columns='urls',
                                          values=urls,
                                          user_id=f"= '{self.__user_id}'",
                                          array=True)
        super()._database.apply_query(query=query_update)


class TMPEvents(BaseType):
    """
    Класс предназначенный для управления ивентами которые не могут сообщить
    о себе пользователю сразу же
    """

    def __init__(self, user_id: str | int):
        self.__user_id = user_id
        self.__user = User(user_id=user_id)

    def get_event(self, filtering: str) -> list[str]:
        """
        Получить ивент по фильтру
        :param filtering: Фильтр по которому был отобран матч
        :type filtering: str
        :return: Список с текстами не дошедших ивентов до пользователя
        :rtype: list[str]
        """
        query = super()._qm_jsonb.read('users', columns='tmp_messages',
                                       path=[filtering],
                                       user_id=f"= '{self.__user.id}'")
        tmp_messages = super()._database.get_one(query=query)
        try:
            return list(filter(None, tmp_messages))
        except TypeError:
            return []

    def set_event(self, message: str, filtering: str):
        """
        Позволяет установить ивент матча
        :param message: Текст будущего ивента
        :type message: str
        :param filtering:  Фильтр по которому был отобран матч
        :type filtering: str
        """

        isnull = not self.get_event(filtering=filtering)
        if isnull is True:
            query = super()._qm_jsonb.update('users', columns='tmp_messages',
                                             path=[filtering],
                                             values=message, array=True,
                                             user_id=f"= '{self.__user.id}'")
        else:
            query = super()._qm_jsonb.unite('users', columns='tmp_messages',
                                            path=[filtering],
                                            values=message, array=True,
                                            user_id=f"= '{self.__user.id}'")
        super()._database.apply_query(query=query)

    def delete_event(self, filtering: str = None):
        """
        Удаляет ивент по фильтру
        :param filtering: Фильтр по которому был отобран матч
        :type filtering: str
        """
        if filtering is None:
            query = super()._qm.update('users', columns=['tmp_messages'],
                                       values=['{}'],
                                       user_id=f"= '{self.__user.id}'")
        else:
            query = (
                    "UPDATE users SET tmp_messages = tmp_messages - '%s'; " %
                    filtering
            )
        super()._database.apply_query(query=query)


class Counters(BaseType):
    """
    Управление счетчиками пользователя
    """

    def __init__(self, user_id: str | int):
        self.__user_id = user_id

    def get_counter(self, filtering: str, type_coincidence: str) -> int:
        user = User(self.__user_id)
        strategy = user.strategy
        bookmaker = 'fonbet'
        sport = 'basketball'
        query = super()._qm_jsonb.read('users', columns='counters',
                                       path=[bookmaker, sport, strategy,
                                             filtering, type_coincidence],
                                       user_id=f"= '{self.__user_id}'")
        counter = super()._database.get_one(query=query)
        return int(counter)


class Match(BaseType):
    """
    Управление матчами
    """

    def __init__(self, match_id: str | int):
        self.__match_id = match_id
        self.__table = 'matches'

    def create(self, data: dict):
        query = super()._qm.create(self.__table,
                                   columns=['id', "timer", "part", 'team1',
                                            'team2', 'filter',
                                            'json_url', 'scores',
                                            'prognoses'],
                                   values=[self.id, data["timer"],
                                           data["part"], data["team1"],
                                           data["team2"], data['filter'],
                                           data['json_url'],
                                           data['scores'],
                                           data['prognoses']])
        return super()._database.apply_query(query=query)

    def update(self, data: dict):
        query = super()._qm.update(self.__table,
                                   columns=["timer", "part", 'scores'],
                                   values=[data["timer"], data["part"],
                                           data['scores']],
                                   id=f"= '{self.id}'")
        return super()._database.apply_query(query=query)

    def delete(self):
        query = super()._qm.delete(self.__table, id=f"= '{self.id}'")
        super()._database.apply_query(
            query=query
        )

    def edit(self, column: str, value: Any):
        query = super()._qm.update(self.__table, columns=column,
                                   values=value,
                                   id=f"= '{self.id}'")
        return super()._database.apply_query(query)

    @property
    def teams(self) -> str:
        query_team1 = super()._qm.read(self.__table, columns='team1',
                                       id=f"= '{self.id}'")

        query_team2 = super()._qm.read(self.__table, columns='team2',
                                       id=f"= '{self.id}'")

        team1 = super()._database.get_one(query_team1)
        team2 = super()._database.get_one(query_team2)
        return f'{team1} - {team2}'

    @property
    def id(self):
        return self.__match_id

    @property
    def all(self):
        query = super()._qm.read(self.__table, columns='*',
                                 id=f"= '{self.id}'")
        return list(map(lambda x: str(x), super()._database.get_more(query)))

    @property
    def timer(self):
        query = super()._qm.read(self.__table, columns='timer',
                                 id=f"= '{self.id}'")
        return super()._database.get_one(query=query)

    @property
    def part(self) -> int:
        query = super()._qm.read(self.__table, columns='part',
                                 id=f"= '{self.id}'")

        return int(super()._database.get_one(query))

    @property
    def status(self):
        query = super()._qm.read(self.__table, columns='status',
                                 id=f"= '{self.id}'")

        return super()._database.get_one(query)

    def set_status(self, new_status: str):
        query = super()._qm.update('users', columns=['status'],
                                   values=new_status,
                                   id=f"= '{self.id}'")
        super()._database.apply_query(query=query)

    @property
    def scores(self) -> Scores:
        query = super()._qm.read(self.__table, columns='scores',
                                 id=f"= '{self.id}'")

        return Scores(super()._database.get_one(query))

    @property
    def bets(self) -> Bet:
        return Bet(self.__match_id)

    @property
    def filter(self) -> str:
        query = super()._qm.read(self.__table, columns='filter',
                                 id=f"= '{self.id}'")

        return super()._database.get_one(query)

    @property
    def json_url(self) -> str:
        query = super()._qm.read(self.__table, columns='json_url',
                                 id=f"= '{self.id}'")

        return super()._database.get_one(query)

    @property
    def in_database(self) -> bool:
        query = super()._qm.read(self.__table, columns='id',
                                 id=f"= '{self.id}'")
        try:
            super()._database.get_one(query)
            return True
        except utils.exceptions.NotFoundError:
            return False

    def template_event_message(self, user_id: str | int, type_coincidence: str):
        bet_ = Bet(self.id)
        teams = self.teams
        filtering = Match(self.id).filter
        bet = bet_.get_bet(self.part + 1)
        result_bet = bet_.get_bet_result(self.part)
        counter = User(user_id=user_id).counter.get_counter(
            filtering=filtering,
            type_coincidence=type_coincidence
        )

        bet_message = 'зашла'
        if not result_bet:
            bet_message = 'не зашла'

        text = (
            f'<b>{teams}</b>\nСтавка {bet_message} {counter} раз подряд\n'
            f'Прогноз на {self.part + 1} - '
            f'{bet}\nСчет'
        )

        return text


class User(BaseType):

    def __init__(self, user_id: str | int):
        self.__user_id = user_id

    def save(self, username: str):
        query = super()._qm.create('users', columns=['user_id', 'username'],
                                   values=[self.__user_id, username])
        super()._database.get_all(query=query)

    def delete(self):
        query = super()._qm.delete('users', user_id=f"= '{self.id}'")
        super()._database.apply_query(query=query)

    def edit(self, column: str, value: Any):
        query = super()._qm.update('users', columns=[column], values=[value],
                                   user_id=f"= '{self.id}'")
        super()._database.apply_query(query=query)

    def matches(self, status: str = 'playing'):
        query = super()._qm.read('matches', columns='id',
                                 status=f"= '{status}'",
                                 id=f"LIKE '%{self.__user_id}%'")
        data = list(map(lambda x: str(x[0]), super()._database.get_all(query)))

        return data

    def is_validate_counter(self, type_coincidence: str, filtering: str):
        counter_query = super()._qm_jsonb.read('users', columns='counters',
                                               path=['fonbet', 'basketball',
                                                     self.strategy,
                                                     filtering,
                                                     type_coincidence],
                                               user_id=f"= '{self.id}'")
        settings_query = super()._qm_jsonb.read('users', columns='settings',
                                                path=['fonbet', 'basketball',
                                                      self.strategy,
                                                      filtering,
                                                      'max_counter'],
                                                user_id=f"= '{self.id}'")

        counter = int(super()._database.get_one(query=counter_query))
        settings = int(super()._database.get_one(query=settings_query))
        return counter >= settings

    def get(self, column: str):
        query = super()._qm.read('users', columns=column,
                                 user_id=f"= '{self.id}'")
        return super()._database.get_one(query=query)

    @property
    def id(self):
        return self.__user_id

    @property
    def info_matches(self):
        return

    @property
    def tmp_events(self) -> TMPEvents:
        return TMPEvents(user_id=self.id)

    @property
    def what_search(self):
        filters_matches = []
        matches_in_db = self.matches(status='playing')
        for match_id in matches_in_db:
            filters_matches.append(Match(match_id=match_id).filter)

        filter_user = self.filters["searching"]
        searching = [x for x in filter_user + filters_matches if
                     x not in filter_user
                     or x not in filters_matches]
        user_filter = self.filters
        user_filter["searching"] = searching
        return user_filter

    @property
    def filters(self) -> dict:
        return super()._database.get_one(
            query=super()._qm.read('users', columns='filters',
                                   user_id=f"= '{self.id}'"))

    @property
    def username(self) -> str:
        query = super()._qm.read('users', columns='username',
                                 user_id=f"= '{self.id}'")
        return super()._database.get_one(query)

    @property
    def is_scanning(self) -> str:
        query = super()._qm.read('users', columns='scanning',
                                 user_id=f"= '{self.id}'")
        return super()._database.get_one(query)

    @property
    def strategy(self) -> str:
        query = super()._qm.read('users', columns='strategy',
                                 user_id=f"= '{self.id}'")
        return super()._database.get_one(query)

    @property
    def counter(self) -> Counters:
        return Counters(self.id)

    @property
    def urls(self) -> Urls:
        return Urls(user_id=self.id)
