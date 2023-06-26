from core.types._base import BaseStrategy
from core.types._base import BaseType
from . import *


class Strategies(BaseType):
    """
    Все стратегии ставок на спорт
    """
    __strategies: list[BaseStrategy] = [Randomaizer(), Scenarios()]

    def __init__(self):
        pass

    @classmethod
    def get_strategy_by_name(cls, name_strategy: str) -> BaseStrategy | None:
        """
        Возвращает объект стратегии
        :param name_strategy: Имя стратегии
        :type name_strategy: str
        :return: Объект стратегии
        :rtype: BaseStrategy
        """

        for strategy in cls.__strategies:
            try:
                if strategy.name.lower().count(name_strategy.lower()):
                    return strategy
            except AttributeError:
                return None

    def get_all(self):
        return self.__strategies
