from core.database.crud import CRUDService, JsonbCRUDService
from core.database.main_database import Database


class BaseType:
    _model = CRUDService()
    _model_jsonb = JsonbCRUDService()
    _database = Database()

    def create(self):
        raise NotImplementedError('Не реализован метод create в классе наследнике')

    def delete(self):
        raise NotImplementedError('Не реализован метод delete в классе наследнике')

    def edit(self):
        raise NotImplementedError('Не реализован метод edit в классе наследнике')
