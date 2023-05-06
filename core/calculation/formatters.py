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