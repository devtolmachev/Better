import json
from typing import Any

from core.strategies import Strategies
from core.types.user import User, Worker
from utils.repositories.base import BaseRepository


class UserRepository(BaseRepository):

    @staticmethod
    async def save(id: str | int, username: str):
        await User(id=id).save(username=username)

    @staticmethod
    async def get_user_workers(user_id: str | int) -> User.get_workers:
        return await User(id=user_id).get_workers()

    @staticmethod
    def get(id: str | int) -> User:
        return User(id)

    async def get_all(self):
        async with super()._database as db:
            query = super()._qm.read('users', columns='id')
            return [
                id
                for row in await db.get_all(query=query)
                for id in row
            ]

    @staticmethod
    async def delete(id: str | int):
        await User(id=id).delete()

    async def add_worker(self,
                         id: str | int,
                         worker_id: str | int | Any,
                         token: str,
                         worker_info: Any = None):
        worker = Worker(id=worker_id)
        await worker.create(
            user_id=id,
            token=token,
            worker_info=worker_info
        )
        filters = Strategies().get_strategy_by_name('random').filters
        await worker.edit(columns='filters', values=filters)
        user = await self.get(id=id).add_worker(token=token)
