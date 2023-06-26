from typing import Any

from core.types.user.workers import Worker
from utils.repositories.base import BaseRepository


class WorkerRepository(BaseRepository):

    def get(self, id: str | int | Any) -> Worker:
        return Worker(id=id)

    def delete(self, id: str | int | Any) -> None:
        Worker(id=id).delete()

    async def get_all(self):
        async with super()._database as db:
            query = self._qm.read('workers', columns='id')
            return [
                value
                for row in await db.get_all(query)
                for value in row
            ]
