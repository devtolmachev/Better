import json
import random

from core.types._base import BaseStrategy
from core.types.matches import Match
from utils.exceptions import UninterestingMatch


class Scenarios(BaseStrategy):
    _filters_dict = {"searching": ["NBA 2K23"],
                     "blacklist": ["NCAA", "NСАА", "H2H LIGA-1"]}
    __max_matches_in_liga = 1
    __sep = '$'

    async def update_counter(self, filtering: str, id: str | int,
                             type_coincidence: str):
        await self.__update_temp_counters(
                type_coincidence=type_coincidence,
                user_id=id
            )

        async with super()._database as db:

            tmp_counter_guess = int(await db.get_one(
                query=super()._qm_jsonb.read('workers', columns='counters',
                                             path=['fonbet', 'basketball',
                                                   self.name,
                                                   'temp_counters', 'guess'],
                                             id=f"= '{id}'")
            ))
            tmp_counter_not_guess = int(await db.get_one(
                query=super()._qm_jsonb.read('workers', columns='counters',
                                             path=['fonbet', 'basketball',
                                                   self.name,
                                                   'temp_counters',
                                                   'not_guess'],
                                             id=f"= '{id}'")
            ))

        if tmp_counter_guess > 0 and tmp_counter_not_guess > 0:
            await self.__reset_temp_counters(user_id=id)
            await self.__reset_main_counters(
                filtering=filtering,
                user_id=id
            )
            raise UninterestingMatch

        elif tmp_counter_guess >= 4 or tmp_counter_not_guess >= 4:
            counter = await self.__update_main_counter(
                type_coincidence=type_coincidence,
                user_id=id, filtering=filtering
            )
            await self.__reset_temp_counters(user_id=id)
            return counter

    async def __update_temp_counters(self,
                                     type_coincidence: str,
                                     user_id: str | int):
        async with super()._database as db:
            new_counter = int(await db.get_one(
                query=super()._qm_jsonb.read('workers', columns='counters',
                                             path=['fonbet', 'basketball',
                                                   self.name,
                                                   'temp_counters',
                                                   type_coincidence],
                                             id=f"= '{user_id}'")
            )) + 1
            query = super()._qm_jsonb.update('workers', columns='counters',
                                             path=['fonbet', 'basketball',
                                                   self.name,
                                                   'temp_counters',
                                                   type_coincidence],
                                             values=new_counter,
                                             id=f"= '{user_id}'")

            await db.apply_query(query=query)

    async def __update_main_counter(self,
                                    type_coincidence: str,
                                    user_id: str | int,
                                    filtering: str):
        async with super()._database as db:
            query = super()._qm_jsonb.read(
                'workers', columns='counters',
                path=['fonbet', 'basketball', self.name,
                      filtering, type_coincidence],
                id=f"= '{user_id}'"
            )
            new_counter = int(await db.get_one(query=query)) + 1
            query = super()._qm_jsonb.update('workers', columns='counters',
                                             path=['fonbet', 'basketball',
                                                   self.name,
                                                   filtering, type_coincidence],
                                             values=new_counter,
                                             id=f"= '{user_id}'")

            await db.apply_query(query)

            main_counter_guess = int(
                await db.get_one(
                    query=super()._qm_jsonb.read('workers', columns='counters',
                                                 path=['fonbet', 'basketball',
                                                       self.name, filtering,
                                                       'guess'],
                                                 id=f"= '{user_id}'")
                )
            )

            main_counter_not_guess = int(
                await db.get_one(
                    query=super()._qm_jsonb.read('workers', columns='counters',
                                                 path=['fonbet', 'basketball',
                                                       self.name, filtering,
                                                       'not_guess'],
                                                 id=f"= '{user_id}'")
                )
            )

            if main_counter_guess > 0 and main_counter_not_guess > 0:
                if type_coincidence == 'guess':
                    type_coincidence = 'not_guess'
                else:
                    type_coincidence = 'guess'

                await db.apply_query(
                    query=super()._qm_jsonb.update('workers',
                                                   columns='counters',
                                                   path=['fonbet', 'basketball',
                                                         self.name, filtering,
                                                         type_coincidence],
                                                   values=0,
                                                   id=f"= '{user_id}'")
                )

            return new_counter

    async def __reset_temp_counters(self,
                                    user_id: str | int):
        async with super()._database as db:
            await db.apply_query(
                query=super()._qm_jsonb.update('workers', columns='counters',
                                               path=['fonbet', 'basketball',
                                                     self.name, 'temp_counters',
                                                     'guess'],
                                               values=0,
                                               id=f"= '{user_id}'")
            )

            await db.apply_query(
                query=super()._qm_jsonb.update('workers', columns='counters',
                                               path=['fonbet', 'basketball',
                                                     self.name, 'temp_counters',
                                                     'not_guess'],
                                               values=0,
                                               id=f"= '{user_id}'")
            )

    async def __reset_main_counters(self,
                                    filtering: str,
                                    user_id: str | int):
        async with super()._database as db:
            await db.apply_query(
                query=super()._qm_jsonb.update('workers', columns='counters',
                                               path=['fonbet', 'basketball',
                                                     self.name, filtering,
                                                     'guess'],
                                               values=0,
                                               id=f"= '{user_id}'")
            )

            await db.apply_query(
                query=super()._qm_jsonb.update('workers', columns='counters',
                                               path=['fonbet', 'basketball',
                                                     self.name, filtering,
                                                     'not_guess'],
                                               values=0,
                                               id=f"= '{user_id}'")
            )

    async def should_let_off_match(self, user_id: str | int):
        async with super()._database as db:
            counter_guess = int(
                await db.get_one(
                    super()._qm_jsonb.read('workers', columns='counters',
                                           path=['fonbet', 'basketball',
                                                 self.name,
                                                 'temp_counters', 'guess'],
                                           id=f"= '{user_id}'")
                )
            )

            counter_not_guess = int(
                await db.get_one(
                    super()._qm_jsonb.read('workers', columns='counters',
                                           path=['fonbet', 'basketball',
                                                 self.name,
                                                 'temp_counters', 'not_guess'],
                                           id=f"= '{user_id}'")
                )
            )

            if counter_guess > 0 and counter_not_guess > 0:
                return True

            return False

    @property
    def filters(self):
        return json.dumps(self._filters_dict, ensure_ascii=False)

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
            self._filters_dict["searching"]
        ) * self.__max_matches_in_liga

    @property
    def max_part(self):
        return 1

    @property
    def max_time(self):
        return '0:59'

    @staticmethod
    async def bet_result(match: Match):
        return await match.bets.get_bet_result(await match.part)

    @staticmethod
    async def template_msg_from_db(match_id: str | int):
        match = Match(id=match_id)

        score = (await match.scores).get_part_score(await match.part)

        message_teams = f"<b>{await match.teams}</b>"
        message_part = f"Играют {await match.part} четверть"
        score_message = f"Счет - {score}"
        timer_message = f"Таймер - {await match.timer}"
        bet_message = f"Выбранный сценарий на матч - " \
                      f"{await match.bets.all_bets}"

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

        bet_result = await match.bets.get_bet_result(await match.part)
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
                     f"подряд{sep}Рекомендую {bet_recommendation}" \
                     f"{sep}{match_id}|{type_coincidence}"

        return event_text
