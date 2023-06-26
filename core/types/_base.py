from core.database.crud import QMService, JsonbQMService, ArrayQMService
from core.database.main import Database


class BaseType:
    """
    Все свойства класса являются вспомогательными сервисами
    """
    _qm = QMService()
    _qm_jsonb = JsonbQMService()
    _qm_array = ArrayQMService()
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


class BaseStrategy(BaseType):
    __sep = '$'
    _filters_dict = {"searching": [...],
                     "blacklist": [...]}

    def update_counter(self, *args, **kwargs):
        raise NotImplementedError(
            'Не реализован метод update_counter в стратегии')

    @property
    def urls_limit(self):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @property
    def part_start(self):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @property
    def sep(self):
        # return self.__sep
        raise NotImplementedError('Наследник должен иметь такой метод')

    @property
    def filters(self):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @staticmethod
    async def template_msg_from_db(match_id: str | int):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @property
    def max_part(self):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @property
    def max_time(self):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @property
    def name(self):
        raise NotImplementedError('Наследник должен иметь такой метод')

    def gen_bets(self, *args, **kwargs):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @staticmethod
    async def bet_result(*args, **kwargs):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @staticmethod
    def template_event(*args, **kwargs):
        raise NotImplementedError('Наследник должен иметь такой метод')

    @property
    def Name(self):
        raise NotImplementedError('Наследник должен иметь такой метод')
