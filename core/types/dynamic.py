from typing import Any, Iterable

import utils.exceptions
from core.calculation.formatters import BetFormatter
from core.types.static import BaseType


class Urls(BaseType):

    def __init__(self, user_id: str | int):
        self.user_id = user_id

    def append(self, url: list):
        query = super()._model.unite('users', column='urls', values=url, user_id=self.user_id)
        super()._database.apply_query(query)

    def get(self):
        query = super()._model.read('users', columns='urls', user_id=self.user_id)

        return super()._database.get_one(query)

    def delete(self, url: list | str):
        query = super()._model.read('users', columns='urls', user_id=self.user_id)
        urls: list = super()._database.get_one(query=query)
        urls.remove(url)
        query_update = super()._model.update('users', columns=['urls'], values=[urls], user_id=self.user_id,
                                             array=True)
        super()._database.apply_query(query=query_update)


class Scores:

    def __init__(self, scores: dict):
        self.__scores = scores

    @property
    def score(self):
        return self.__scores

    def get_part_score(self, part: int, team_num: int = None):
        if not team_num:
            return f'{self.__scores[f"t1_p{part}"]} - {self.__scores[f"t2_p{part}"]}'

        return self.__scores[f"t{team_num}_p{part}"]

    def format_score(self, teams: int = 2) -> str:
        data = []

        total = ':'.join([v for k, v in self.__scores.items() if '0' in k])

        for v in list(self.__scores.values())[teams:]:
            if len(data) == 0:
                data.append(f"{v}")
            elif (len(data) % teams) == 0:
                data.append(f" {v}")
            else:
                data.append(f"-{v}")

        text = f"{total} ({''.join(data)})"
        return text


class TMPMessage(BaseType):

    def __init__(self, user_id: str | int):
        self.__user_id = user_id

    def get_tmp_messages(self, filtering: str) -> list:
        query = super()._model_jsonb.read('users', columns='tmp_messages',
                                          path=[filtering], user_id=self.__user_id)
        tmp_messages = super()._database.get_one(query=query)
        try:
            return list(filter(None, tmp_messages))
        except TypeError:
            return []

    def set_tmp_message(self, message: str, filtering: str):
        isnull = not self.get_tmp_messages(filtering=filtering)
        if isnull is True:
            query = super()._model_jsonb.update('users', column='tmp_messages', path=[filtering],
                                                value=message, array=True, user_id=self.__user_id)
        else:
            query = super()._model_jsonb.unite('users', column='tmp_messages', path=[filtering],
                                               value=message, array=True, user_id=self.__user_id)
        super()._database.apply_query(query=query)

    def delete_tmp_message(self, filtering: str = None):
        if filtering is None:
            query = super()._model.update('users', columns=['tmp_messages'], values=['{}'],
                                          user_id=self.__user_id)
        else:
            query = """UPDATE users SET tmp_messages = tmp_messages - '%s'; """ % filtering
        super()._database.apply_query(query=query)

    def get_info_matches(self, filtering: str) -> tuple[list, Any]:
        query = super()._model_jsonb.read('users', columns='info_matches',
                                          path=[filtering], user_id=self.__user_id)
        tmp_messages = super()._database.get_one(query=query)
        return tmp_messages, filtering

    def set_info_matches(self, match_id: str | int, filtering: str, sep: Any = '$'):
        isnull = not self.get_info_matches(filtering=filtering)
        query_scores = """SELECT scores FROM cache_matches WHERE id = '%s'""" % match_id
        value = dict(sorted(super()._database.get_one(query=query_scores).items(), key=lambda x: x[0][-1]))
        format_score = Scores(value).format_score(teams=2)
        teams = Match(match_id, cache=True).teams
        bets = Match(match_id, cache=True).bets.all_bets
        info = f'{teams}{sep}{format_score}{sep}{bets}'
        if isnull is True:
            query = super()._model_jsonb.update('users', column='info_matches', path=[cache_event_id],
                                                value=info, user_id=self.__user_id)
        else:
            query = super()._model_jsonb.unite('users', column='info_matches', path=[cache_event_id],
                                               value=info, user_id=self.__user_id)
        super()._database.apply_query(query=query)

    def delete_info_matches(self):
        query = super()._model.update('users', columns=['info_matches'], values=['{}'],
                                      user_id=self.__user_id)
        super()._database.apply_query(query=query)


class Counters(BaseType):

    def __init__(self, user_id: str | int):
        self.__user_id = user_id

    def get_validate_counter_value(self, filtering: str, type_coincidence: str):
        user = User(user_id=self.__user_id)
        strategy = user.strategy
        bookmaker = 'fonbet'
        sport = 'basketball'
        query = super()._model_jsonb.read('users', columns=['counters'],
                                          path=[bookmaker, sport, strategy, filtering, type_coincidence])
        counter = super()._database.get_one(query=query)
        return counter


class User(BaseType):

    def __init__(self, user_id: str | int):
        self.__user_id = user_id

    def save(self, username: str):
        query = super()._model.create('users', columns=['user_id', 'username'], values=[self.__user_id, username])
        super()._database.get_all(query=query)

    def delete(self):
        query = super()._model.delete('users', user_id=self.__user_id)
        super()._database.apply_query(query=query)

    def edit(self, column: str, value: Any):
        query = super()._model.update('users', columns=[column], values=[value],
                                      user_id=self.__user_id)
        super()._database.apply_query(query=query)

    def matches(self, status: str = 'playing'):
        tmp = {f"{self.id}": []}
        query = super()._model.read('matches', columns=['id'], status=status)
        data = list(map(lambda x: str(x[0]), super()._database.get_all(query)))
        for id_match in data:
            if id_match.count(str(self.id)):
                tmp[f"{self.id}"].append(id_match)

        return tmp[f"{self.id}"]

    def is_validate_counter(self, type_coincidence: str, filtering: str):
        counter_query = super()._model_jsonb.read('users', columns='counters',
                                                  path=['fonbet', 'basketball', self.strategy,
                                                        filtering, type_coincidence],
                                                  user_id=self.id)
        settings_query = super()._model_jsonb.read('users', columns='settings',
                                                   path=['fonbet', 'basketball', self.strategy, filtering,
                                                         'max_counter'],
                                                   user_id=self.id)

        counter = int(super()._database.get_one(query=counter_query))
        settings = int(super()._database.get_one(query=settings_query))
        return counter >= settings

    def get(self, column: str):
        query = super()._model.read('users', columns=column, user_id=self.id)
        return super()._database.get_one(query=query)

    @property
    def id(self):
        return self.__user_id

    @property
    def info_matches(self):
        return

    @property
    def tmp_messages(self) -> TMPMessage:
        return TMPMessage(user_id=self.id)

    @property
    def what_search(self):
        filters_matches = []
        matches_in_db = self.matches(status='playing')
        for match_id in matches_in_db:
            filters_matches.append(Match(match_id=match_id).filter)

        filter_user = self.filters["searching"]
        searching = [x for x in filter_user + filters_matches if x not in filter_user
                     or x not in filters_matches]
        user_filter = self.filters
        user_filter["searching"] = searching
        return user_filter

    @property
    def filters(self) -> dict:
        return super()._database.get_one(query=super()._model.read('users', columns='filters', user_id=self.id))

    @property
    def username(self) -> str:
        query = super()._model.read('users', columns='username', user_id=self.id)
        return super()._database.get_one(query)

    @property
    def is_scanning(self) -> str:
        query = super()._model.read('users', columns='scanning', user_id=self.id)
        return super()._database.get_one(query)

    @property
    def strategy(self) -> str:
        query = super()._model.read('users', columns='strategy', user_id=self.id)
        return super()._database.get_one(query)

    @property
    def counter(self) -> Counters:
        return Counters(self.id)

    @property
    def urls(self) -> Urls:
        return Urls(user_id=self.__user_id)

    @property
    def settings(self):
        return Urls(user_id=self.__user_id)


class Bet(BaseType):

    def __init__(self, match_id: str):
        self.__match_id = match_id

    @property
    def last_bet(self):
        part = int(super()._database.get_one(
            query=super()._model.read('matches', columns='part', id=self.__match_id))
        )
        last_bet_query = super()._model_jsonb.read('matches', columns='prognoses',
                                                   path=[f'part{part}'],
                                                   id=self.__match_id)
        return super()._database.get_one(query=last_bet_query)

    def get_bet(self, part: int | str):
        query = super()._model_jsonb.read('matches', columns='prognoses', path=[f'part{part}'],
                                          id=self.__match_id)
        return super()._database.get_one(query=query)

    @property
    def all_bets(self):
        bets = []
        query = super()._model_jsonb.read('matches', columns='prognoses', path=None, id=self.__match_id)
        for k, v in super()._database.get_one(query).items():
            bets.append(v)
        return ', '.join(bets)

    def get_bet_result(self, part: int = None):
        """
        Сверяет свою ставку, с реальным счетом
        :param part: Период/тайм/четверть которую вы хотите сверить. Если указано None, то по возможности бот проверит
            предыдущую ставку
        :type part:
        :return:
        :rtype:
        """
        formatter = BetFormatter()

        if not part:
            get_part_query = super()._model.read('matches', columns='part', id=self.__match_id)
            part_now = super()._database.get_one(get_part_query)
            get_score_query = super()._model.read('matches', columns='scores', id=self.__match_id)

            score = super()._database.get_one(get_score_query)
            lst = [score[f"t1_p{part_now}"], score[f't2_p{part_now}']]
            exodus = formatter.even_format(lst)
            if self.last_bet.lower() == exodus.lower():
                return True
            else:
                return False

        get_score_query = super()._model.read('matches', columns='scores', id=self.__match_id)

        score = super()._database.get_one(get_score_query)
        lst = [score[f"t1_p{part}"], score[f't2_p{part}']]
        exodus = formatter.even_format(lst)
        if self.get_bet(part).lower() == exodus.lower():
            return True
        else:
            return False


class CacheMatches(BaseType):

    def __init__(self, match_id: Any):
        self.__match_id = match_id

    def delete(self):
        query = super()._model.delete('cache_matches', id=self.__match_id)
        super()._database.apply_query(query=query)

    def create(self, table: str = 'cache_matches'):
        query = """INSERT INTO %s SELECT * FROM matches WHERE id = ('%s')""" % (table, self.__match_id)
        super()._database.apply_query(query=query)

    def is_cached(self):
        try:
            query = super()._model.read('cache_matches', columns=['id'], id=self.__match_id)
            match_cache = super()._database.get_one(query=query)
            return bool(match_cache)
        except utils.exceptions.NotFoundError:
            pass

    @staticmethod
    def delete_cache_matches(user_id: int | str):
        for match_id in User(user_id=user_id).tmp_messages.get_cached_events_ids():
            CacheMatches(match_id=match_id).delete()


class Match(BaseType):

    def __init__(self, match_id: str | int, cache: bool = False):
        self.__match_id = match_id
        self.__table = 'matches'
        if cache:
            self.__table = 'cache_matches'

    def create(self, data: dict):
        query = super()._model.create(self.__table, columns=['id', "timer", "part", 'team1', 'team2', 'filter',
                                                             'json_url', 'scores', 'prognoses'],
                                      values=[self.__match_id, data["timer"], data["part"], data["team1"],
                                              data["team2"], data['filter'], data['json_url'],
                                              data['scores'], data['prognoses']])
        return super()._database.apply_query(query=query)

    @property
    def cache(self) -> CacheMatches:
        return CacheMatches(self.__match_id)

    def update(self, data: dict):
        query = super()._model.update(self.__table, columns=["timer", "part", 'scores'],
                                      values=[data["timer"], data["part"], data['scores']], id=self.__match_id)
        print(query)
        return super()._database.apply_query(query=query)

    def delete(self):
        super()._database.apply_query(
            query=super()._model.delete(self.__table, id=self.__match_id)
        )

    def edit(self, column: str, value: Any):
        query = super()._model.update(self.__table, columns=[column], values=[value])
        return super()._database.apply_query(query)

    @property
    def teams(self) -> str:
        query_team1 = super()._model.read(self.__table, columns='team1', id=self.__match_id)

        query_team2 = super()._model.read(self.__table, columns='team2', id=self.__match_id)

        team1 = super()._database.get_one(query_team1)
        team2 = super()._database.get_one(query_team2)
        return f'{team1} - {team2}'

    @property
    def all(self):
        query = super()._model.read(self.__table, columns='*', id=self.__match_id)
        return list(map(lambda x: str(x), super()._database.get_more(query)))

    @property
    def timer(self):
        query = super()._model.read(self.__table, columns='timer', id=self.__match_id)
        return super()._database.get_one(query=query)

    @property
    def part(self) -> int:
        query = super()._model.read(self.__table, columns='part', id=self.__match_id)

        return int(super()._database.get_one(query))

    @property
    def status(self):
        query = super()._model.read(self.__table, columns='status', id=self.__match_id)

        return super()._database.get_one(query)

    def set_status(self, new_status: str):
        query = super()._model.update('users', columns=['status'], values=new_status,
                                      id=self.__match_id)
        super()._database.apply_query(query=query)

    @property
    def scores(self) -> Scores:
        query = super()._model.read(self.__table, columns='scores', id=self.__match_id)

        return Scores(super()._database.get_one(query))

    @property
    def bets(self) -> Bet:
        query = super()._model.read(self.__table, columns='prognoses', id=self.__match_id)

        return Bet(self.__match_id)

    @property
    def filter(self) -> str:
        query = super()._model.read(self.__table, columns='filter', id=self.__match_id)

        return super()._database.get_one(query)

    @property
    def json_url(self) -> str:
        query = super()._model.read(self.__table, columns='json_url', id=self.__match_id)

        return super()._database.get_one(query)

    @property
    def in_database(self) -> bool:
        query = super()._model.read(self.__table, columns='id', id=self.__match_id)
        try:
            super()._database.get_one(query)
            return True
        except utils.exceptions.NotFoundError:
            return False

    def template_event_message(self, user_id: str | int, type_coincidence: str):
        bet_ = Bet(self.__match_id)
        teams = self.teams
        filtering = Match(self.__match_id).filter
        score = self.scores.get_part_score(self.part)
        bet = bet_.get_bet(self.part + 1)
        result_bet = bet_.get_bet_result(self.part)
        counter = User(user_id=user_id).counter.get_validate_counter_value(filtering=filtering,
                                                                           type_coincidence=type_coincidence)

        bet_message = 'зашла'
        if not result_bet:
            bet_message = 'не зашла'

        text = f'<b>{teams}</b>\nСтавка {bet_message} {counter} раз подряд\nПрогноз на {self.part + 1} - ' \
               f'{bet}\nСчет'
