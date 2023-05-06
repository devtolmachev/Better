import json
import random

from loguru import logger

from core.better import Better
from core.types.static import BaseType
from utils.exceptions import UninterestingMatch


class BaseStrategy(BaseType):

    @staticmethod
    def _bet_result(user_id: str | int, event_id: str | int,
                    quater: int | None = None, total: bool | None = None):
        """
        Этот метод проверяет прогноз

        :param user_id: Telegram user_id

        :param event_id: Идентификатор матча

        :param quater: Проверяемая четверть. Исход четверти - прогноз на четверть

        :param total: Если нужно проверить общий тотал матча, указывайте True
        """
        with Better() as better:
            bet: str = better.previous_bet

            if bet.lower().count("пропускаю"):
                logger.debug('Вернул "pass"')
                return 'pass'

            key = None
            if quater is not None:
                key = 'score'

            elif total is not None:
                key = 'total'

            logger.debug(f'Key -> {key}')

            score = better.select_all_data_about_match(user_id=user_id,
                                                       event_id=event_id,
                                                       quater=quater)[key]. \
                split(" - ")

            word_for_loguru = f'{quater} четверти'

            if total:
                word_for_loguru = f'тотала'

            logger.debug(f'Счет {word_for_loguru} -> {score}')

            result_score = None
            if (int(score[0]) + int(score[1])) % 2 == 0:
                result_score = 'ЧЕТ'
            elif (int(score[0]) + int(score[1])) % 2 == 1:
                result_score = 'НЕЧЕТ'

            if result_score == bet:
                return 'guess'

            elif result_score != bet:
                return 'not_guess'

    @property
    def filters(self):
        return

    @property
    def max_part(self):
        return

    @property
    def max_time(self):
        return

    @property
    def name(self):
        return 'Base'


class Randomaizer(BaseStrategy):
    __filters_dict = {"searching": ["NBA 2K23", ""], "blacklist": ["NCAA", "NСАА"]}
    __max_matches_in_liga = 1

    @staticmethod
    def gen_bets(quater: int, prognos_now_quater: bool,
                 prognos_total: bool = True) -> list:
        """
        Используйте этот метод, чтобы сгенерировать прогноз для стратегии "рандомайзер"

        :param quater: Укажите текущую четверть матча

        :param prognos_now_quater: Укажите True если нужно начать генерацию прогноза со
            следущей четверти.
            Укажите False если нужно пропустить генерацию прогноза на текущую четверть

        :param prognos_total: Нужно ли делать прогнозы на общий тотал?

        :return: Возвращает список со сгенерированными прогнозами для стратегии
            "Рандомайзер"
        """

        prognos_lst = []
        query = None

        match prognos_now_quater:
            case True:
                quater -= 1
                query = len(prognos_lst) <= quater
            case False:
                query = len(prognos_lst) < quater

        if quater == 4:
            quater = 3

        while True:
            if quater == 0:
                while True:
                    for x in [random.randint(1, 101) % 2,
                              random.randint(1, 101) % 2]:
                        if len(prognos_lst) == 3:
                            if prognos_total is True:
                                prognos_lst.append(random.choice(["ЧЕТ", "НЕЧЕТ"]))
                            return prognos_lst

                        if x == 0:
                            prognos_lst.append('ЧЕТ')
                        elif x == 1:
                            prognos_lst.append('НЕЧЕТ')

            else:
                prognos_lst.append('ПРОПУСКАЮ ЭТУ ЧЕТВЕРТЬ')
                if len(prognos_lst) == quater:
                    while True:
                        for x in [random.randint(1, 101) % 2,
                                  random.randint(1, 101) % 2]:
                            if len(prognos_lst) == 3:
                                if prognos_total is True:
                                    prognos_lst.append(
                                        random.choice(["ЧЕТ", "НЕЧЕТ"]))
                                return prognos_lst

                            else:
                                if x == 0:
                                    prognos_lst.append('ЧЕТ')
                                else:
                                    prognos_lst.append('НЕЧЕТ')

    def update_counter(self, user_id: str | int, filtering: str, type_coincidence: str, *args, **kwargs):
        return self.__update_counters(user_id=user_id, filtering=filtering, type_coincidence=type_coincidence)

    def __update_counters(self, user_id: str | int, filtering: str, type_coincidence: str):
        counter_guess = int(
            super()._database.get_one(
                query=super()._model_jsonb.read('users', column='counters', path=['fonbet', 'basketball', self.name,
                                                                                  filtering, 'guess'],
                                                user_id=user_id)
            )
        )

        counter_not_guess = int(
            super()._database.get_one(
                query=super()._model_jsonb.read('users', column='counters', path=['fonbet', 'basketball', self.name,
                                                                                  filtering, 'not_guess'],
                                                user_id=user_id)
            )
        )
        if counter_guess > 0 and counter_not_guess > 0:
            self.reset_counters(user_id=user_id, filtering=filtering)

        counter = int(
            super()._database.get_one(
                query=super()._model_jsonb.read('users', column='counters', path=['fonbet', 'basketball', self.name,
                                                                                  filtering, type_coincidence],
                                                user_id=user_id)
            )
        ) + 1

        if counter_guess > 0 and type_coincidence == 'not_guess':
            super()._database.apply_query(
                query=super()._model_jsonb.update(
                    'users', column='counters', value=0, path=['fonbet', 'basketball', self.name, filtering,
                                                               'guess'],
                    user_id=user_id
                )
            )

        elif counter_not_guess > 0 and type_coincidence == 'guess':
            super()._database.apply_query(
                query=super()._model_jsonb.update(
                    'users', column='counters', value=0, path=['fonbet', 'basketball', self.name, filtering,
                                                               'not_guess'],
                    user_id=user_id
                )
            )

        query_update = super()._model_jsonb.update('users', column='counters',
                                                   path=['fonbet', 'basketball', self.name, filtering,
                                                         type_coincidence],
                                                   value=counter,
                                                   user_id=user_id)

        super()._database.apply_query(query=query_update)
        return counter

    def reset_counters(self, user_id: int | str, filtering: str):
        super()._database.apply_query(
            query=super()._model_jsonb.update('users', column='counters',
                                              path=['fonbet', 'basketball', self.name, filtering, 'guess'],
                                              value=0,
                                              user_id=user_id)
        )

        super()._database.apply_query(
            query=super()._model_jsonb.update('users', column='counters',
                                              path=['fonbet', 'basketball', self.name, filtering, 'not_guess'],
                                              value=0,
                                              user_id=user_id)
        )

    @staticmethod
    def should_let_off_match(*args, **kwargs):
        pass

    @property
    def filters(self):
        return json.dumps(self.__filters_dict)

    @property
    def max_part(self):
        return 3

    @property
    def max_time(self):
        return 5.00

    @property
    def name(self):
        return 'random'

    @property
    def urls_limit(self):
        return len(self.__filters_dict["searching"]) * self.__max_matches_in_liga


class Scenarios(BaseStrategy):
    __filters_dict = {"searching": ["NBA 2K23"], "blacklist": ["NCAA", "NСАА", "H2H LIGA-1"]}
    __max_matches_in_liga = 1

    def update_counter(self, filtering: str, user_id: str | int, type_coincidence: str):
        self.__update_temp_counters(type_coincidence=type_coincidence,
                                    user_id=user_id)

        tmp_counter_guess = int(super()._database.get_one(
            query=super()._model_jsonb.read('users', column='counters', path=['fonbet', 'basketball', self.name,
                                                                              'temp_counters', 'guess'])
        ))
        tmp_counter_not_guess = int(super()._database.get_one(
            query=super()._model_jsonb.read('users', column='counters', path=['fonbet', 'basketball', self.name,
                                                                              'temp_counters', 'not_guess'])
        ))

        if tmp_counter_guess > 0 and tmp_counter_not_guess > 0:
            self.__reset_temp_counters()
            self.__reset_main_counters(filtering=filtering)
            raise UninterestingMatch

        elif tmp_counter_guess >= 4 or tmp_counter_not_guess >= 4:
            counter = self.__update_main_counter(type_coincidence=type_coincidence,
                                                 user_id=user_id, filtering=filtering)
            self.__reset_temp_counters()
            return counter

    def __update_temp_counters(self, type_coincidence: str, user_id: str | int):
        new_counter = int(super()._database.get_one(
            super()._model_jsonb.read('users', column='counters', path=['fonbet', 'basketball', self.name,
                                                                        'temp_counters', type_coincidence],
                                      user_id=user_id)
        )) + 1
        query = super()._model_jsonb.update('users', column='counters', path=['fonbet', 'basketball', self.name,
                                                                              'temp_counters', type_coincidence],
                                            value=new_counter, user_id=user_id)

        super()._database.apply_query(query)

    def __update_main_counter(self, type_coincidence: str, user_id: str | int, filtering: str):
        new_counter = int(super()._database.get_one(
            super()._model_jsonb.read('users', column='counters', path=['fonbet', 'basketball', self.name,
                                                                        filtering, type_coincidence],
                                      user_id=user_id)
        )) + 1
        query = super()._model_jsonb.update('users', column='counters', path=['fonbet', 'basketball', self.name,
                                                                              filtering, type_coincidence],
                                            value=new_counter, user_id=user_id)

        super()._database.apply_query(query)

        main_counter_guess = int(
            super()._database.get_one(
                query=super()._model_jsonb.read('users', column='counters', path=['fonbet', 'basketball',
                                                                                  self.name, filtering,
                                                                                  'guess'],
                                                user_id=user_id)
            )
        )

        main_counter_not_guess = int(
            super()._database.get_one(
                query=super()._model_jsonb.read('users', column='counters', path=['fonbet', 'basketball',
                                                                                  self.name, filtering,
                                                                                  'not_guess'],
                                                user_id=user_id)
            )
        )

        if main_counter_guess > 0 and main_counter_not_guess > 0:
            if type_coincidence == 'guess':
                type_coincidence = 'not_guess'
            else:
                type_coincidence = 'guess'

            super()._database.apply_query(
                query=super()._model_jsonb.update('users', column='counters', path=['fonbet', 'basketball',
                                                                                    self.name, filtering,
                                                                                    type_coincidence],
                                                  value=0, user_id=user_id)
            )

        return new_counter

    def __reset_temp_counters(self):
        super()._database.apply_query(
            query=super()._model_jsonb.update('users', column='counters', path=['fonbet', 'basketball',
                                                                                self.name, 'temp_counters',
                                                                                'guess'],
                                              value=0)
        )

        super()._database.apply_query(
            query=super()._model_jsonb.update('users', column='counters', path=['fonbet', 'basketball',
                                                                                self.name, 'temp_counters',
                                                                                'not_guess'],
                                              value=0)
        )

    def __reset_main_counters(self, filtering: str):
        super()._database.apply_query(
            query=super()._model_jsonb.update('users', column='counters', path=['fonbet', 'basketball',
                                                                                self.name, filtering,
                                                                                'guess'],
                                              value=0)
        )

        super()._database.apply_query(
            query=super()._model_jsonb.update('users', column='counters', path=['fonbet', 'basketball',
                                                                                self.name, filtering,
                                                                                'not_guess'],
                                              values=0)
        )

    def should_let_off_match(self, user_id: str | int):
        counter_guess = int(
            super()._database.get_one(
                super()._model_jsonb.read('users', column='counters', path=['fonbet', 'basketball', self.name,
                                                                            'temp_counters', 'guess'],
                                          user_id=user_id)
            )
        )

        counter_not_guess = int(
            super()._database.get_one(
                super()._model_jsonb.read('users', column='counters', path=['fonbet', 'basketball', self.name,
                                                                            'temp_counters', 'not_guess'],
                                          user_id=user_id)
            )
        )

        if counter_guess > 0 and counter_not_guess > 0:
            return True

        return False

    @property
    def filters(self):
        return json.dumps(self.__filters_dict)

    @staticmethod
    def gen_bets(*args, **kwargs) -> list:
        all_scenarios = [['ЧЕТ', 'ЧЕТ', 'ЧЕТ', 'ЧЕТ'],
                         ['НЕЧЕТ', 'НЕЧЕТ', 'НЕЧЕТ', 'НЕЧЕТ'],
                         ['ЧЕТ', 'ЧЕТ', 'ЧЕТ', 'НЕЧЕТ'],
                         ['НЕЧЕТ', 'НЕЧЕТ', 'НЕЧЕТ', 'ЧЕТ'],
                         ['ЧЕТ', 'ЧЕТ', 'НЕЧЕТ', 'НЕЧЕТ'],
                         ['НЕЧЕТ', 'НЕЧЕТ', 'ЧЕТ', 'ЧЕТ'],
                         ['ЧЕТ', 'НЕЧЕТ', 'НЕЧЕТ', 'НЕЧЕТ'],
                         ['НЕЧЕТ', 'ЧЕТ', 'ЧЕТ', 'ЧЕТ'],
                         ['ЧЕТ', 'ЧЕТ', 'НЕЧЕТ', 'ЧЕТ'],
                         ['НЕЧЕТ', 'НЕЧЕТ', 'ЧЕТ', 'НЕЧЕТ'],
                         ['ЧЕТ', 'НЕЧЕТ', 'ЧЕТ', 'ЧЕТ'],
                         ['НЕЧЕТ', 'ЧЕТ', 'НЕЧЕТ', 'НЕЧЕТ'],
                         ['ЧЕТ', 'НЕЧЕТ', 'ЧЕТ', 'НЕЧЕТ'],
                         ['НЕЧЕТ', 'ЧЕТ', 'НЕЧЕТ', 'ЧЕТ'],
                         ['ЧЕТ', 'НЕЧЕТ', 'НЕЧЕТ', 'ЧЕТ'],
                         ['НЕЧЕТ', 'ЧЕТ', 'ЧЕТ', 'НЕЧЕТ']]

        random_scenarios = random.choice(all_scenarios)
        return random_scenarios

    @property
    def name(self):
        return 'scenarios'

    @property
    def urls_limit(self):
        return len(self.__filters_dict["searching"]) * self.__max_matches_in_liga
