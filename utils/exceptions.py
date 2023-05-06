from loguru import logger

from typing import Any


class BaseBetterExceptions(Exception):
    pass


class WrongQueryError(BaseBetterExceptions):
    message = 'Wrong Database Query'

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(logger.error(self.message))


class WrongJsonbQueryError(BaseBetterExceptions):
    message = 'Wrong Database Query'

    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__(logger.error(self.message))


class BaseFonbetException(Exception):
    """
    Базовые исключения для бота (этого проекта)
    """


class MatchFinishError(Exception):
    """"Это исключение вызывается, когда заканчивается матч"""

    message = 'Матч кончился. Ищу следующий'

    def __init__(self, message: Any = None):
        if message:
            self.message = message
        super().__init__(logger.critical(self.message))


class UninterestingMatch(Exception):
    """Это исключение вызывается в том случае, когда матч по определенным причинам
    становится не интересным"""

    message = 'Этот матч стал неинтересным, отслеживание отменяется'

    def __init__(self, message: Any = None):
        if message:
            self.message = message
        super().__init__(logger.critical(self.message))


class RetryError(Exception):
    """Исключение вызывается в том случае, если нужно повторить попытку"""
    message = 'Попытка подключиться заново'

    def __init__(self, message: Any = None):
        if message:
            self.message = message
        super().__init__(logger.critical(self.message))


class MatchesNotFoundError(Exception):
    """Исключение возникает когда матч(и) не найден(ы)"""

    message = 'Матчи не найдены'

    def __init__(self, message: Any = None):
        if message:
            self.message = message
        super().__init__(logger.critical(self.message))


class WrongLeaguesFilter(Exception):
    """Возникает в случае, если были переданы неправильно фильтры"""

    message = 'Неправильно переданы фильтры с лигами'

    def __init__(self, message: Any = None):
        if message:
            self.message = message
        super().__init__(logger.error(self.message))


class WrongJsonbQuery(Exception):
    """
    Возникает в том случае, если был неправильно сформирован запрос в БД,
    при типе данных jsonb
    """

    message = 'Неправильный запрос в базу данных при типе данных jsonb'

    def __init__(self, message: Any = None):
        if message:
            self.message = message
        super().__init__(logger.critical(self.message))


class NotFoundError(Exception):
    """
    Возникает в том случае, если в базе данных после запроса ничего не найдено (возвращается None)
    """

    message = 'В базе данных ничего не найдено!'

    def __init__(self, message: Any = None):
        if message:
            self.message = message
        super().__init__(logger.error(self.message))


class UninterestingMatch:
    """
    Возникает в том случае, если матч по правилам стратегии не интересный, и его надо убрать
    """

    message = 'Матч не интересен, начинаю поиск другого'

    def __init__(self, message: Any = None):
        if message:
            self.message = message
        super().__init__(logger.error(self.message))

