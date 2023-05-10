from core.types.dynamic import User, Bet, Match
from core.types.static import BaseType


class BaseRepository(BaseType):
    """
    Базовый репозиторий для всех классов
    """

    def get(self):
        raise NotImplementedError('Не реализован метод get в классе наследнике')

    def save(self):
        raise NotImplementedError('Не реализован метод save в классе наследнике')

    def delete(self):
        raise NotImplementedError('Не реализован метод delete в классе наследнике')


class UserRepository(BaseRepository):

    @staticmethod
    def save(user_id: str | int, username: str):
        User(user_id=user_id).save(username=username)

    def get(self, user_id: str | int) -> User:
        return User(user_id)

    def get_all(self):
        query = self._model.read('users', columns='user_id')
        return list(map(lambda x: str(x[0]), super()._database.get_all(query)))

    @staticmethod
    def delete(user_id: str | int):
        User(user_id=user_id).delete()

    @staticmethod
    def set_scanning(user_id: str | int, status: bool = True):
        User(user_id=user_id).edit(column='scanning', value=status)

    @staticmethod
    def add_url(user_id: str | int, url: list):
        User(user_id=user_id).urls.append(url)


class MatchRepository(BaseRepository):

    @staticmethod
    def get(match_id) -> Match:
        return Match(match_id=match_id)

    @staticmethod
    def delete(match_id: str):
        Match(match_id=match_id).delete()

    @staticmethod
    def create(match_id: str, data: dict):
        Match(match_id=match_id).create(data)

    @staticmethod
    def set_status(match_id: str, new_status: str):
        Match(match_id=match_id).edit(column='status', value=new_status)

    def get_matches(self) -> list[str]:
        query = super()._model.read('matches', columns='id')
        return list(map(lambda x: str(x[0]), super()._database.get_all(query=query)))
