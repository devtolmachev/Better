import json
import random

from core.types._base import BaseStrategy
from core.types.matches import Match


# noinspection PyPropertyDefinition
class Randomaizer(BaseStrategy):
    _filters_dict = {"searching": ["", "NBA 2K23"],
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

    async def update_counter(self, id: str | int, filtering: str,
                             type_coincidence: str, *args, **kwargs):
        return await self.__update_counters(
            id=id, filtering=filtering,
            type_coincidence=type_coincidence
        )

    async def __update_counters(self, id: str | int, filtering: str,
                                type_coincidence: str):
        async with super()._database as db:
            counter_guess = int(
                await db.get_one(
                    query=super()._qm_jsonb.read(
                        'workers', columns='counters',
                        path=['fonbet', 'basketball',
                              self.name,
                              filtering, 'guess'],
                        id=f"= '{id}'"
                    )
                )
            )

            counter_not_guess = int(
                await db.get_one(
                    query=super()._qm_jsonb.read('workers', columns='counters',
                                                 path=['fonbet', 'basketball',
                                                       self.name,
                                                       filtering, 'not_guess'],
                                                 id=f"= '{id}'")
                )
            )

            if counter_guess > 0 and counter_not_guess > 0:
                await self.reset_counters(id=id, filtering=filtering)

            if counter_guess > 0 and type_coincidence == 'not_guess':
                await db.apply_query(
                    query=super()._qm_jsonb.update(
                        'workers', columns='counters', values=0,
                        path=['fonbet', 'basketball', self.name, filtering,
                              'guess'],
                        id=f"= '{id}'"
                    )
                )

            elif counter_not_guess > 0 and type_coincidence == 'guess':
                await db.apply_query(
                    query=super()._qm_jsonb.update(
                        'workers', columns='counters', values=0,
                        path=['fonbet', 'basketball', self.name, filtering,
                              'not_guess'],
                        id=f"= '{id}'"
                    )
                )

            counter = int(
                await db.get_one(
                    query=super()._qm_jsonb.read('workers', columns='counters',
                                                 path=['fonbet', 'basketball',
                                                       self.name,
                                                       filtering,
                                                       type_coincidence],
                                                 id=f"= '{id}'")
                )
            ) + 1

            query_update = super()._qm_jsonb.update('workers',
                                                    columns='counters',
                                                    path=['fonbet',
                                                          'basketball',
                                                          self.name, filtering,
                                                          type_coincidence],
                                                    values=counter,
                                                    id=f"= '{id}'")

            await db.apply_query(query=query_update)
            return counter

    async def reset_counters(self, id: int | str, filtering: str):
        async with super()._database as db:
            for type_coincidence in ['guess', 'not_guess']:
                await db.apply_query(
                    query=super()._qm_jsonb.update('workers',
                                                   columns='counters',
                                                   path=['fonbet', 'basketball',
                                                         self.name, filtering,
                                                         type_coincidence],
                                                   values=0,
                                                   id=f"= '{id}'")
                )

    @staticmethod
    def should_let_off_match(*args, **kwargs):
        pass

    @property
    def filters(self):
        return json.dumps(ensure_ascii=False, obj=self._filters_dict)

    @property
    def max_part(self):
        return 4

    async def bet_result(self,
                         match: Match,
                         part: int = None,
                         *args, **kwargs):

        if part is None:
            part = await match.part

        if part >= 4:
            return await match.bets.get_bet_result(0)
        else:
            return await match.bets.get_bet_result(part)

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
            self._filters_dict["searching"]
        ) * self.__max_matches_in_liga

    @staticmethod
    async def template_msg_from_db(match_id: str | int):
        match = Match(id=match_id)
        score = (await match.scores).get_part_score(await match.part)

        message_teams = f"<b>{await match.teams}</b>"
        message_part = f"Играют {await match.part} четверть"
        score_message = f"Счет - {score}"
        timer_message = f"Таймер - {await match.timer}"
        bet_message = f"Ставка на {await match.part} четверть - " \
                      f"{await match.bets.get_bet(await match.part)}"
        if await match.part > 3:
            bet_message = f"Ставка на матч - {await match.bets.get_bet(0)}"

        text = (f"{message_teams}\n{message_part}\n"
                f"{score_message}\n{timer_message}\n"
                f"{bet_message}")
        return text

    @property
    def Name(self):
        return f"{self.name[0].upper()}{self.name[1:].lower()}"

    async def template_event(
            self,
            match_id: str,
            type_coincidence: str,
            counter: int | str,
            sep: str = '$',
            *args, **kwargs
    ):
        self.__sep = sep
        match = Match(id=match_id)

        if not type_coincidence.count('pass'):

            if await match.part >= 4:
                part = 0
            else:
                part = await match.part

            bet_result = await match.bets.get_bet_result(part=part)
            guess_msg = "угадал"
            bet_recommendation = 'идти в обратку'
            if not bet_result:
                guess_msg = 'не угадал'
                bet_recommendation = 'идти по моему прогнозу'

            event_text = f"Я {guess_msg} {counter} подряд{sep}" \
                         f"Рекомендую {bet_recommendation}{sep}{match_id}%" \
                         f"{type_coincidence}"

        else:
            event_text = str(sep)

        return event_text
