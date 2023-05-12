from core.database.crud import QMService
from core.database.repositories import UserRepository, MatchRepository
from core.database.main_database import Database
from core.types.matches import Bet
from core.types.user import User


class Better(Database, UserRepository, MatchRepository, Bet):
    _qm = QMService()

    def __init__(self):
        super().__init__()

    def __enter__(self):
        super().__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)

    @staticmethod
    def get_user(user_id) -> User:
        user = UserRepository()
        return user.get(user_id=user_id)
