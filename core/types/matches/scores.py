from core.types._base import BaseType


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

        sorted_score = sorted(
            list(self.__scores.items()), key=lambda x: x[0][-1]
        )[teams:]

        for k, v in sorted_score:
            if len(data) == 0:
                data.append(f"{v}")
            elif (len(data) % teams) == 0:
                data.append(f" {v}")
            else:
                data.append(f"-{v}")

        text = f"{total} ({''.join(data)})"
        return text
