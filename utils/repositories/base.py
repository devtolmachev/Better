from core.types._base import BaseType


class BaseRepository(BaseType):
    """
    Базовый репозиторий для всех классов
    """

    def get(self):
        raise NotImplementedError('Не реализован метод get в классе '
                                  'наследнике')

    def save(self):
        raise NotImplementedError('Не реализован метод save в классе '
                                  'наследнике')

    def delete(self):
        raise NotImplementedError('Не реализован метод delete в классе '
                                  'наследнике')
