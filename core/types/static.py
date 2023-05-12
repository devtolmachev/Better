from core.database.crud import QMService, JsonbQMService
from core.database.main_database import Database


class BaseType:
    """
    Все свойства класса являются вспомогательными сервисами
    """
    _qm = QMService()
    _qm_jsonb = JsonbQMService()
    _database = Database()

    def create(self):
        raise NotImplementedError(
            'Не реализован метод create в классе наследнике')

    def delete(self):
        raise NotImplementedError(
            'Не реализован метод delete в классе наследнике')

    def edit(self):
        raise NotImplementedError(
            'Не реализован метод edit в классе наследнике')
