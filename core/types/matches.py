from core.calculation.formatters import BetFormatter
from core.types.static import BaseType


class Scores(BaseType):
    """
    Управляет счетом матчей
    """

    def __init__(self, scores: dict):
        """
        Передайте счет.
        :param scores: Счет команд. Должен быть словарем, где ключи должны
             быть такого формата "t{номер команды}_p{номер периода/четверти}"
        :type scores: dict
        """
        self.__scores = scores

    @property
    def score(self):
        """Возвращает счет в неизмененном виде"""
        return self.__scores

    def get_part_score(self, part: int, team_num: int = None) -> str:
        """
        Получить счет конкретного периода
        :param part: Номер четверти
        :type part: int
        :param team_num: Номер команды - если указано None, то метод вернет
            счет обеих команд формата - (счет 1 команды - счет 2 команды)
        :type team_num: int
        :return: Счет конкретного периода
        :rtype: int
        """
        if not team_num:
            return f'{self.__scores[f"t1_p{part}"]} ' \
                   f'- {self.__scores[f"t2_p{part}"]}'

        return self.__scores[f"t{team_num}_p{part}"]

    def format_score_fonbet(self, teams: int = 2) -> str:
        """
        Форматирует счет в удобно читаемый формат как на фонбете.
        Пример - 38:37 (10-10 12-13 7-8 9-16)
        :param teams: Количество команд
        :type teams: int
        :return: Счет в красивом виде как на фонбете
        :rtype: str
        """
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


class Bet(BaseType):
    """
    Управление ставкой/ставками
    """

    def __init__(self, match_id: str):
        self.__match_id = match_id

    @property
    def last_bet(self) -> str:
        """
        Получает и возвращает ставку для последней части (тайма, четверти)
            матча
        :return: Ставку в виде строки
        :rtype: str
        """
        query = super()._qm.read('matches', columns='part',
                                 id=f"= '{self.__match_id}'")
        part = int(super()._database.get_one(query=query))

        last_bet_query = super()._qm_jsonb.read('matches',
                                                columns='prognoses',
                                                path=[f'part{part}'],
                                                id=f"= '{self.__match_id}'")
        return super()._database.get_one(query=last_bet_query)

    def get_bet(self, part: int | str):
        """
        Получает и возвращает ставку в строковом виде для конкретной части
        (периода, тайма, или четверти) матча
        :param part: Часть матча для которой нужно получить ставку
        :type part: int
        :return: Ставку в строковом виде
        :rtype: str
        """
        query = super()._qm_jsonb.read('matches', columns='prognoses',
                                       path=[f'part{part}'],
                                       id=f"= '{self.__match_id}'")
        return super()._database.get_one(query=query)

    @property
    def all_bets(self):
        """
        Возвращает все ставки формата (ЧЕТ, ЧЕТ, ЧЕТ, ЧЕТ)
        :return: Все ставки
        :rtype: str
        """
        bets = []
        query = super()._qm_jsonb.read('matches', columns='prognoses',
                                       path=None, id=f"= '{self.__match_id}'")
        bets_dict = super()._database.get_one(query)

        for k, v in sorted(bets_dict.items(), key=lambda x: x[0][-1]):
            bets.append(v)
        return f"({', '.join(bets)})"

    def get_bet_result(self, part: int = None) -> bool | str:
        """
        Сверяет свою ставку, с реальным счетом
        :param part: Период/тайм/четверть которую вы хотите сверить.
            Если указано None, то по возможности бот проверит предыдущую ставку
        :type part:
        :return:
        :rtype:
        """
        formatter = BetFormatter()

        if part is None:
            get_part_query = super()._qm.read('matches', columns='part',
                                              id=f"= '{self.__match_id}'")
            part_now = super()._database.get_one(get_part_query)
            get_score_query = super()._qm.read('matches', columns='scores',
                                               id=f"= '{self.__match_id}'")

            score = super()._database.get_one(get_score_query)
            lst = [score[f"t1_p{part_now}"], score[f't2_p{part_now}']]
            exodus = formatter.even_format(lst)
            bet = self.last_bet.lower()
            if bet.lower().count('пропускаю'):
                return 'pass'
            if bet == exodus.lower():
                return True
            else:
                return False

        get_score_query = super()._qm.read('matches', columns='scores',
                                           id=f"= '{self.__match_id}'")

        score = super()._database.get_one(get_score_query)
        lst = [score[f"t1_p{part}"], score[f't2_p{part}']]
        exodus = formatter.even_format(lst)
        bet = self.get_bet(part).lower()
        if bet.lower().count('пропускаю'):
            return 'pass'
        if bet == exodus.lower():
            return True
        else:
            return False
