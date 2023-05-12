import json
import random

from loguru import logger

from core.better import Better
from core.database.repositories import UserRepository, MatchRepository
from core.types.matches import Bet
from core.types.static import BaseType
from utils.exceptions import UninterestingMatch


class BaseStrategy(BaseType):
    __sep = '$'

    @staticmethod
    def _bet_result(user_id: str | int, event_id: str | int,
                    part: int | None = None, total: bool | None = None):
        """
        Этот метод проверяет прогноз

        :param user_id: Telegram user_id

        :param event_id: Идентификатор матча

        :param part: Проверяемая четверть. Исход четверти - прогноз на
            четверть

        :param total: Если нужно проверить общий тотал матча, указывайте True
        """
        with Better() as better:
            bet: str = better.last_bet

            if bet.lower().count("пропускаю"):
                logger.debug('Вернул "pass"')
                return 'pass'

            key = None
            if part is not None:
                key = 'score'

            elif total is not None:
                key = 'total'

            logger.debug(f'Key -> {key}')

            score = better.select_all_data_about_match(user_id=user_id,
                                                       event_id=event_id,
                                                       quater=part)[key]. \
                split(" - ")

            word_for_loguru = f'{part} четверти'

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

    def update_counter(self, *args, **kwargs):
        raise NotImplementedError(
            'Не реализован метод update_counter в стратегии')

    @property
    def part_start(self):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @property
    def sep(self):
        # return self.__sep
        raise NotImplementedError('Наследник должен иметь такой метод')

    @property
    def filters(self):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @property
    def max_part(self):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @property
    def max_time(self):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @property
    def name(self):
        raise NotImplementedError('Наследник должен иметь такой метод')

    def gen_bets(self, *args, **kwargs):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @staticmethod
    def bet_result(*args, **kwargs):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @staticmethod
    def template_event(*args, **kwargs):
        raise NotImplementedError('Наследник должен иметь такой метод')


class Randomaizer(BaseStrategy):
    __filters_dict = {"searching": ["", "NBA 2K23"],
                      "blacklist": ["NCAA", "NСАА"]}
    __max_matches_in_liga = 1
    __sep = '$'

    @staticmethod
    def gen_bets(part: int, prognos_now_quater: bool,
                 prognos_total: bool = True) -> list:
        """
        Используйте этот метод, чтобы сгенерировать прогноз для стратегии
        "рандомайзер"

        :param part: Укажите текущую часть матча

        :param prognos_now_quater: Укажите True если нужно начать генерацию
            прогноза со следущей части матча.
            Укажите False если нужно пропустить генерацию прогноза на текущую
            часть

        :param prognos_total: Нужно ли делать прогнозы на общий счет?

        :return: Возвращает список со сгенерированными прогнозами для стратегии
            "Рандомайзер"
        """

        prognos_lst = []

        if part == 4:
            part = 3

        if prognos_total is True:
            prognos_lst.append(
                random.choice(["ЧЕТ", "НЕЧЕТ"]))

        while True:
            cond = (len(prognos_lst) - 1) == part
            if prognos_now_quater:
                cond = (part - len(prognos_lst) + 1) == 1
            if part == 0:
                while True:
                    for x in [random.randint(1, 101) % 2,
                              random.randint(1, 101) % 2]:
                        if len(prognos_lst) == 5:
                            return prognos_lst

                        if x == 0:
                            prognos_lst.append('ЧЕТ')
                        elif x == 1:
                            prognos_lst.append('НЕЧЕТ')

            else:
                if cond:
                    while True:
                        for x in [random.randint(1, 101) % 2,
                                  random.randint(1, 101) % 2]:
                            if len(prognos_lst) == 5:
                                return prognos_lst

                            else:
                                if x == 0:
                                    prognos_lst.append('ЧЕТ')
                                else:
                                    prognos_lst.append('НЕЧЕТ')
                else:
                    prognos_lst.append('ПРОПУСКАЮ ЭТУ ЧЕТВЕРТЬ')

    def update_counter(self, user_id: str | int, filtering: str,
                       type_coincidence: str, *args, **kwargs):
        return self.__update_counters(user_id=user_id, filtering=filtering,
                                      type_coincidence=type_coincidence)

    def __update_counters(self, user_id: str | int, filtering: str,
                          type_coincidence: str):
        counter_guess = int(
            super()._database.get_one(
                query=super()._qm_jsonb.read('users', columns='counters',
                                             path=['fonbet', 'basketball',
                                                   self.name,
                                                   filtering, 'guess'],
                                             user_id=f"= '{user_id}'")
            )
        )

        counter_not_guess = int(
            super()._database.get_one(
                query=super()._qm_jsonb.read('users', columns='counters',
                                             path=['fonbet', 'basketball',
                                                   self.name,
                                                   filtering, 'not_guess'],
                                             user_id=f"= '{user_id}'")
            )
        )
        if counter_guess > 0 and counter_not_guess > 0:
            self.reset_counters(user_id=user_id, filtering=filtering)

        if counter_guess > 0 and type_coincidence == 'not_guess':
            super()._database.apply_query(
                query=super()._qm_jsonb.update(
                    'users', columns='counters', values=0,
                    path=['fonbet', 'basketball', self.name, filtering,
                          'guess'],
                    user_id=f"= '{user_id}'"
                )
            )

        elif counter_not_guess > 0 and type_coincidence == 'guess':
            super()._database.apply_query(
                query=super()._qm_jsonb.update(
                    'users', columns='counters', values=0,
                    path=['fonbet', 'basketball', self.name, filtering,
                          'not_guess'],
                    user_id=f"= '{user_id}'"
                )
            )

        counter = int(
            super()._database.get_one(
                query=super()._qm_jsonb.read('users', columns='counters',
                                             path=['fonbet', 'basketball',
                                                   self.name,
                                                   filtering,
                                                   type_coincidence],
                                             user_id=f"= '{user_id}'")
            )
        ) + 1

        query_update = super()._qm_jsonb.update('users', columns='counters',
                                                path=['fonbet', 'basketball',
                                                      self.name, filtering,
                                                      type_coincidence],
                                                values=counter,
                                                user_id=f"= '{user_id}'")

        super()._database.apply_query(query=query_update)
        return counter

    def reset_counters(self, user_id: int | str, filtering: str):
        super()._database.apply_query(
            query=super()._qm_jsonb.update('users', columns='counters',
                                           path=['fonbet', 'basketball',
                                                 self.name, filtering,
                                                 'guess'],
                                           values=0,
                                           user_id=f"= '{user_id}'")
        )

        super()._database.apply_query(
            query=super()._qm_jsonb.update('users', columns='counters',
                                           path=['fonbet', 'basketball',
                                                 self.name, filtering,
                                                 'not_guess'],
                                           values=0,
                                           user_id=f"= '{user_id}'")
        )

    @staticmethod
    def should_let_off_match(*args, **kwargs):
        pass

    @property
    def filters(self):
        return json.dumps(self.__filters_dict)

    @property
    def max_part(self):
        return 4

    def bet_result(self, match: MatchRepository.get):
        part = match.part
        if part >= 4:
            return Bet(match.id).get_bet_result(0)
        else:
            return Bet(match.id).get_bet_result(part)

    @property
    def sep(self):
        return self.__sep

    @property
    def part_start(self):
        return 0

    @property
    def max_time(self):
        return False

    @property
    def name(self):
        return 'random'

    @property
    def urls_limit(self):
        return len(
            self.__filters_dict["searching"]) * self.__max_matches_in_liga

    @staticmethod
    def template_msg_from_db(user_id: str | int, match_id: str | int):
        match = MatchRepository().get(match_id=match_id)

        message_teams = f"<b>{match.teams}</b>"
        message_part = f"Играют {match.part} четверть"
        score_message = f"Счет - {match.scores.get_part_score(match.part)}"
        timer_message = f"Таймер - {match.timer}"
        bet_message = f"Ставка на {match.part} четверть - " \
                      f"{match.bets.get_bet(match.part)}"
        if match.part > 3:
            bet_message = f"Ставка на матч - {match.bets.get_bet(0)}"

        text = (f"{message_teams}\n{message_part}\n"
                f"{score_message}\n{timer_message}\n"
                f"{bet_message}")
        return text

    def template_event(self, user_id: str | int, match_id: str, filtering: str,
                       type_coincidence: str, sep: str = '$', *args, **kwargs):
        self.__sep = sep
        user = UserRepository().get(user_id=user_id)
        match = MatchRepository().get(match_id=match_id)

        counter = user.counter.get_counter(filtering=filtering,
                                           type_coincidence=type_coincidence)
        bet_result = match.bets.get_bet_result(match.part)
        guess_msg = "угадал"
        bet_recommendation = 'идти в обратку'
        if not bet_result:
            guess_msg = 'не угадал'
            bet_recommendation = 'идти по моему прогнозу'

        event_text = f"Я {guess_msg} {counter} подряд{sep}" \
                     f"Рекомендую {bet_recommendation}"

        return event_text


class Scenarios(BaseStrategy):
    __filters_dict = {"searching": ["NBA 2K23"],
                      "blacklist": ["NCAA", "NСАА", "H2H LIGA-1"]}
    __max_matches_in_liga = 1
    __sep = '$'

    def update_counter(self, filtering: str, user_id: str | int,
                       type_coincidence: str):
        self.__update_temp_counters(type_coincidence=type_coincidence,
                                    user_id=user_id)

        tmp_counter_guess = int(super()._database.get_one(
            query=super()._qm_jsonb.read('users', columns='counters',
                                         path=['fonbet', 'basketball',
                                               self.name,
                                               'temp_counters', 'guess'],
                                         user_id=f"= '{user_id}'")
        ))
        tmp_counter_not_guess = int(super()._database.get_one(
            query=super()._qm_jsonb.read('users', columns='counters',
                                         path=['fonbet', 'basketball',
                                               self.name,
                                               'temp_counters', 'not_guess'],
                                         user_id=f"= '{user_id}'")
        ))

        if tmp_counter_guess > 0 and tmp_counter_not_guess > 0:
            self.__reset_temp_counters(user_id=user_id)
            self.__reset_main_counters(filtering=filtering,
                                       user_id=user_id)
            raise UninterestingMatch

        elif tmp_counter_guess >= 4 or tmp_counter_not_guess >= 4:
            counter = self.__update_main_counter(
                type_coincidence=type_coincidence,
                user_id=user_id, filtering=filtering
            )
            self.__reset_temp_counters(user_id=user_id)
            return counter

    def __update_temp_counters(self, type_coincidence: str, user_id: str | int):
        new_counter = int(super()._database.get_one(
            super()._qm_jsonb.read('users', columns='counters',
                                   path=['fonbet', 'basketball', self.name,
                                         'temp_counters', type_coincidence],
                                   user_id=f"= '{user_id}'")
        )) + 1
        query = super()._qm_jsonb.update('users', columns='counters',
                                         path=['fonbet', 'basketball',
                                               self.name,
                                               'temp_counters',
                                               type_coincidence],
                                         values=new_counter,
                                         user_id=f"= '{user_id}'")

        super()._database.apply_query(query)

    def __update_main_counter(self, type_coincidence: str, user_id: str | int,
                              filtering: str):
        query = super()._qm_jsonb.read('users', columns='counters',
                                       path=['fonbet', 'basketball', self.name,
                                             filtering, type_coincidence],
                                       user_id=f"= '{user_id}'")
        new_counter = int(super()._database.get_one(query=query)) + 1
        query = super()._qm_jsonb.update('users', columns='counters',
                                         path=['fonbet', 'basketball',
                                               self.name,
                                               filtering, type_coincidence],
                                         values=new_counter,
                                         user_id=f"= '{user_id}'")

        super()._database.apply_query(query)

        main_counter_guess = int(
            super()._database.get_one(
                query=super()._qm_jsonb.read('users', columns='counters',
                                             path=['fonbet', 'basketball',
                                                   self.name, filtering,
                                                   'guess'],
                                             user_id=f"= '{user_id}'")
            )
        )

        main_counter_not_guess = int(
            super()._database.get_one(
                query=super()._qm_jsonb.read('users', columns='counters',
                                             path=['fonbet', 'basketball',
                                                   self.name, filtering,
                                                   'not_guess'],
                                             user_id=f"= '{user_id}'")
            )
        )

        if main_counter_guess > 0 and main_counter_not_guess > 0:
            if type_coincidence == 'guess':
                type_coincidence = 'not_guess'
            else:
                type_coincidence = 'guess'

            super()._database.apply_query(
                query=super()._qm_jsonb.update('users', columns='counters',
                                               path=['fonbet', 'basketball',
                                                     self.name, filtering,
                                                     type_coincidence],
                                               values=0,
                                               user_id=f"= '{user_id}'")
            )

        return new_counter

    def __reset_temp_counters(self, user_id: str | int):
        super()._database.apply_query(
            query=super()._qm_jsonb.update('users', columns='counters',
                                           path=['fonbet', 'basketball',
                                                 self.name, 'temp_counters',
                                                 'guess'],
                                           values=0,
                                           user_id=f"= '{user_id}'")
        )

        super()._database.apply_query(
            query=super()._qm_jsonb.update('users', columns='counters',
                                           path=['fonbet', 'basketball',
                                                 self.name, 'temp_counters',
                                                 'not_guess'],
                                           values=0,
                                           user_id=f"= '{user_id}'")
        )

    def __reset_main_counters(self, filtering: str, user_id: str | int):
        super()._database.apply_query(
            query=super()._qm_jsonb.update('users', columns='counters',
                                           path=['fonbet', 'basketball',
                                                 self.name, filtering,
                                                 'guess'],
                                           values=0,
                                           user_id=f"= '{user_id}'")
        )

        super()._database.apply_query(
            query=super()._qm_jsonb.update('users', columns='counters',
                                           path=['fonbet', 'basketball',
                                                 self.name, filtering,
                                                 'not_guess'],
                                           values=0,
                                           user_id=f"= '{user_id}'")
        )

    def should_let_off_match(self, user_id: str | int):
        counter_guess = int(
            super()._database.get_one(
                super()._qm_jsonb.read('users', columns='counters',
                                       path=['fonbet', 'basketball',
                                             self.name,
                                             'temp_counters', 'guess'],
                                       user_id=f"= '{user_id}'")
            )
        )

        counter_not_guess = int(
            super()._database.get_one(
                super()._qm_jsonb.read('users', columns='counters',
                                       path=['fonbet', 'basketball',
                                             self.name,
                                             'temp_counters', 'not_guess'],
                                       user_id=f"= '{user_id}'")
            )
        )

        if counter_guess > 0 and counter_not_guess > 0:
            return True

        return False

    @property
    def filters(self):
        return json.dumps(self.__filters_dict)

    @property
    def sep(self):
        return self.__sep

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
    def part_start(self):
        return 1

    @property
    def name(self):
        return 'scenarios'

    @property
    def urls_limit(self):
        return len(
            self.__filters_dict["searching"]) * self.__max_matches_in_liga

    @property
    def max_part(self):
        return 1

    @staticmethod
    def bet_result(match: MatchRepository.get):
        return Bet(match.id).get_bet_result(match.part)

    @property
    def max_time(self):
        return '5:59'

    @staticmethod
    def template_msg_from_db(user_id: str | int, match_id: str | int):
        user = UserRepository().get(user_id=user_id)
        match = MatchRepository().get(match_id=match_id)

        message_teams = f"<b>{match.teams}</b>"
        message_part = f"Играют {match.part} четверть"
        score_message = f"Счет - {match.scores.get_part_score(match.part)}"
        timer_message = f"Таймер - {match.timer}"
        bet_message = f"Выбранный сценарий на матч - {match.bets.all_bets}"

        text = (f"{message_teams}\n{message_part}\n"
                f"{score_message}\n{timer_message}\n"
                f"{bet_message}")
        return text

    def template_event(self, user_id: str | int, match_id: str, filtering: str,
                       type_coincidence: str, sep: str = '$'):
        self.__sep = sep
        user = UserRepository().get(user_id=user_id)
        match = MatchRepository().get(match_id=match_id)

        counter = user.counter.get_counter(filtering=filtering,
                                           type_coincidence=type_coincidence)
        bet_result = match.bets.get_bet_result(match.part)
        guess_msg = "угадал"
        bet_recommendation = 'идти в обратку'
        if not bet_result:
            guess_msg = 'не угадал'
            bet_recommendation = 'идти по моему прогнозу'

        scenario = 'сценарий'
        if 5 >= counter >= 2:
            scenario = 'сценария'
        elif counter > 5:
            scenario = 'сценариев'

        event_text = f"Я полностью {guess_msg} {counter} {scenario} " \
                     f"подряд{sep}Рекомендую {bet_recommendation}"

        return event_text
