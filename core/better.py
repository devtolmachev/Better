from core.database.crud import CRUDService
from core.database.main_database import Database
from core.database.repositories import MatchRepository, UserRepository
from core.types.dynamic import User, Bet


class Better(Database, UserRepository, MatchRepository, Bet):
    _model = CRUDService()

    def __init__(self):
        super().__init__()

    def __enter__(self):
        super().__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)

    @staticmethod
    def get_user(user_id) -> User:
        user = UserRepository(user_id=user_id)
        return user.get(user_id=user_id)
