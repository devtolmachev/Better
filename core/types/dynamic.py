from typing import Any

import utils.exceptions
from core.calculation.formatters import BetFormatter
from core.types.static import BaseType


class UrlsUser(BaseType):

    def __init__(self, user_id: str | int):
        self.user_id = user_id

    def append(self, url: list):
        query = super()._model.unite('users', column='urls', values=url, user_id=self.user_id)
        super()._database.get_all(query)

    def get(self):
        query = super()._model.read('users', column='urls', user_id=self.user_id)

        return super()._database.get_one(query)

    def delete(self, url: list | str):
        query = super()._model.read('users', column='urls', user_id=self.user_id)
        urls: list = super()._database.get_one(query=query)
        urls.remove(url)
        query_update = super()._model.update('users', columns=['urls'], values=[urls], user_id=self.user_id,
                                             array=True)
        super()._database.apply_query(query=query_update)


class Bets:

    def __init__(self, prognoses: dict):
        self.__prognoses = prognoses

    def get_part_bet(self, part: int):
        return self.__prognoses[f"part{part}"]


class Scores:

    def __init__(self, scores: dict):
        self.__scores = scores

    @property
    def score(self):
        return self.__scores

    def get_part_score(self, part: int, team_num: int):
        return self.__scores[f"t{team_num}_p{part}"]


class Counters(BaseType):

    def __init__(self, user_id: str | int, strategy: str):
        self.__user_id = user_id
        self.__strategy = strategy


class Settings:

    def __init__(self):
        pass


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

    def update_counter(self, type_coincidence: str):
        new_counter = int(super()._database.get_one(
            super()._model_jsonb.read('users', column='counters', path=['fonbet', 'basketball', self.strategy,
                                                                        'temp_counters', type_coincidence],
                                      user_id=self.id)
        )) + 1
        query = super()._model_jsonb.update('users', column='counters', path=['fonbet', 'basketball', self.strategy,
                                                                              'temp_counters', type_coincidence],
                                            value=new_counter)
        super()._database.apply_query(query)

    def is_validate_counter(self, type_coincidence: str, filtering: str):
        counter_query = super()._model_jsonb.read('users', column='counters',
                                                  path=['fonbet', 'basketball', self.strategy,
                                                        filtering, type_coincidence],
                                                  user_id=self.id)
        settings_query = super()._model_jsonb.read('users', column='settings',
                                                   path=['fonbet', 'basketball', self.strategy, filtering,
                                                         'max_counter'],
                                                   user_id=self.id)

        counter = int(super()._database.get_one(query=counter_query))
        settings = int(super()._database.get_one(query=settings_query))
        return counter >= settings

    @property
    def id(self):
        return self.__user_id

    @property
    def username(self) -> str:
        query = super()._model.read('users', column='username', user_id=self.id)
        return super()._database.get_one(query)

    @property
    def is_scanning(self) -> str:
        query = super()._model.read('users', column='scanning', user_id=self.id)
        return super()._database.get_one(query)

    @property
    def strategy(self) -> str:
        query = super()._model.read('users', column='strategy', user_id=self.id)
        return super()._database.get_one(query)

    @property
    def counter(self) -> Counters:
        return Counters(self.id)

    @property
    def urls(self) -> UrlsUser:
        return UrlsUser(user_id=self.__user_id)

    @property
    def settings(self):
        return UrlsUser(user_id=self.__user_id)

    def get_info(self, column_):
        query = super()._model.read('users', column=column_, user_id=self.id)
        return super()._database.get_one(query)


class Bet(BaseType):

    def __init__(self, match_id: str):
        self.__match_id = match_id

    @property
    def previous_bet(self) -> str:
        get_part_query = super()._model.read('matches', column='part', id=self.__match_id)
        part = super()._database.get_one(get_part_query)
        get_bet_query = super()._model_jsonb.read('matches', column='prognoses', id=self.__match_id,
                                                  path=[f"part{part}"])

        return super()._database.get_one(get_bet_query)

    def part_bet(self, part: int):
        query = super()._model_jsonb.read('matches', column='prognoses',
                                          id=self.__match_id, path=[f"part{part}"])

        return super()._database.get_one(query)

    @property
    def abs_bet(self):
        query = super()._model_jsonb.read('matches', column='prognoses', path=None, id=self.__match_id)
        return list(map(lambda x: str(x), super()._database.get_one(query)))

    def compare_bet_with_score(self, part: int = None):
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
            get_part_query = super()._model.read('matches', column='part', id=self.__match_id)
            part_now = super()._database.get_one(get_part_query)
            get_score_query = super()._model.read('matches', column='scores', id=self.__match_id)

            score = super()._database.get_one(get_score_query)
            lst = [score[f"t1_p{part_now}"], score[f't2_p{part_now}']]
            exodus = formatter.even_format(lst)
            if self.previous_bet.lower() == exodus.lower():
                return True
            else:
                return False

        get_score_query = super()._model.read('matches', column='scores', id=self.__match_id)

        score = super()._database.get_one(get_score_query)
        lst = [score[f"t1_p{part}"], score[f't2_p{part}']]
        exodus = formatter.even_format(lst)
        if self.part_bet(part).lower() == exodus.lower():
            return True
        else:
            return False


class Match(BaseType):

    def __init__(self, match_id: str | int):
        self.__match_id = match_id

    def create(self, data: dict):
        query = super()._model.create('matches', columns=['id', "timer", "part", 'team1', 'team2', 'filter',
                                                          'json_url', 'scores', 'prognoses'],
                                      values=[self.__match_id, data["timer"], data["part"], data["team1"],
                                              data["team2"], data['filter'], data['json_url'],
                                              data['scores'], data['prognoses']])
        return super()._database.apply_query(query=query)

    def update(self, data: dict):
        query = super()._model.update('matches', columns=["timer", "part", 'scores'],
                                      values=[data["timer"], data["part"], data['scores']], id=self.__match_id)
        print(query)
        return super()._database.apply_query(query=query)

    def delete(self):
        super()._database.apply_query(
            query=super()._model.delete('matches', id=self.__match_id)
        )

    def edit(self, column: str, value: str):
        query = super()._model.update('scores', columns=[column], values=[value])
        return super()._database.apply_query(query)

    @property
    def teams(self) -> str:
        query_team1 = super()._model.read('matches', column='team1', id=self.__match_id)

        query_team2 = super()._model.read('matches', column='team2', id=self.__match_id)

        team1 = super()._database.get_one(query_team1)
        team2 = super()._database.get_one(query_team2)
        return f'{team1} - {team2}'

    @property
    def part(self) -> int:
        query = super()._model.read('matches', column='part', id=self.__match_id)

        return int(super()._database.get_one(query))

    @property
    def status(self):
        query = super()._model.read('matches', column='status', id=self.__match_id)

        return super()._database.get_one(query)

    @property
    def scores(self) -> Scores:
        query = super()._model.read('matches', column='scores', id=self.__match_id)

        return Scores(super()._database.get_one(query))

    @property
    def bets(self) -> Bets:
        query = super()._model.read('matches', column='prognoses', id=self.__match_id)

        return Bets(super()._database.get_one(query))

    @property
    def filter(self) -> str:
        query = super()._model.read('matches', column='filter', id=self.__match_id)

        return super()._database.get_one(query)

    @property
    def json_url(self):
        query = super()._model.read('matches', column='json_url', id=self.__match_id)

        return super()._database.get_one(query)

    @property
    def in_database(self):
        query = super()._model.read('matches', column='id', id=self.__match_id)

        try:
            return super()._database.get_one(query)
        except utils.exceptions.NotFoundError:
            return False
