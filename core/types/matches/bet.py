import loguru

from core.types._base import BaseType


class BetFormatter:

    @staticmethod
    def even_format(score: list) -> str:
        """
        Форматирует счет в чет/нечет
        :param score: Счет 2 команд. Например - [10, 10]
        :type score: list
        :return:
        :rtype:
        """

        if (int(score[0]) + int(score[1])) % 2 == 0:
            return 'чет'
        else:
            return 'нечет'


class Bet(BaseType):
    """
    Управление ставкой/ставками
    """

    def __init__(self, match_id: str):
        self.__match_id = match_id

    @property
    async def last_bet(self) -> str:
        """
        Получает и возвращает ставку для последней части (тайма, четверти)
            матча
        :return: Ставку в виде строки
        :rtype: str
        """
        async with super()._database as db:
            query = super()._qm.read(
                'matches', columns='part',
                id=f"= '{self.__match_id}'"
            )
            part = int(await db.get_one(query=query))

            last_bet_query = super()._qm_jsonb.read(
                'matches',
                columns='prognoses',
                path=[f'part{part}'],
                id=f"= '{self.__match_id}'"
            )

            bet = await db.get_one(query=last_bet_query)

        return bet

    async def get_bet(self, part: int | str):
        """
        Получает и возвращает ставку в строковом виде для конкретной части
        (периода, тайма, или четверти) матча
        :param part: Часть матча для которой нужно получить ставку
        :type part: int
        :return: Ставку в строковом виде
        :rtype: str
        """
        async with super()._database as db:
            query = super()._qm_jsonb.read(
                'matches', columns='prognoses',
                path=[f'part{part}'],
                id=f"= '{self.__match_id}'"
            )

            result = await db.get_one(query=query)

        return result

    @property
    async def all_bets(self):
        """
        Возвращает все ставки формата (ЧЕТ, ЧЕТ, ЧЕТ, ЧЕТ)
        :return: Все ставки
        :rtype: str
        """
        async with super()._database as db:
            bets = []

            query = super()._qm_jsonb.read(
                'matches', columns='prognoses',
                path=None, id=f"= '{self.__match_id}'"
            )

            bets_dict = await db.get_one(query)

            for k, v in sorted(bets_dict.items(), key=lambda x: x[0][-1]):
                bets.append(v)

        return f"({', '.join(bets)})"

    async def get_bet_result(self, part: int = None) -> bool | str:
        """
        Сверяет свою ставку, с реальным счетом
        :param part: Период/тайм/четверть которую вы хотите сверить.
            Если указано None, то по возможности бот проверит предыдущую ставку
        :type part:
        :return:
        :rtype:
        """
        async with super()._database as db:
            formatter = BetFormatter()

            if part is None:
                get_part_query = super()._qm.read(
                    'matches', columns='part',
                    id=f"= '{self.__match_id}'"
                )
                part_now = await db.get_one(get_part_query)
                get_score_query = super()._qm.read(
                    'matches', columns='scores',
                    id=f"= '{self.__match_id}'"
                )

                score = await db.get_one(
                    get_score_query
                )
                lst = [score[f"t1_p{part_now}"], score[f't2_p{part_now}']]
                exodus = formatter.even_format(lst)
                bet = await self.last_bet
                bet = bet.lower()

                if bet.lower().count('пропускаю'):
                    return 'pass'
                if bet == exodus.lower():
                    return True
                else:
                    return False

            get_score_query = super()._qm.read('matches', columns='scores',
                                               id=f"= '{self.__match_id}'")

            score = await db.get_one(query=get_score_query)

            lst = [score[f"t1_p{part}"], score[f't2_p{part}']]
            exodus = formatter.even_format(lst)
            bet = await self.get_bet(part)
            bet = bet.lower()
            if bet.lower().count('пропускаю'):
                return 'pass'
            if bet == exodus.lower():
                return True
            else:
                return False
