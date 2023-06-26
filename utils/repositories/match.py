import asyncio
from typing import Any

from core.types.matches import Match
from utils.repositories.base import BaseRepository


class MatchRepository(BaseRepository):

    @staticmethod
    def get(match_id) -> Match:
        return Match(id=match_id)

    @staticmethod
    async def delete(match_id: str):
        await Match(id=match_id).delete()

    @staticmethod
    async def create(match_id: str, data: dict):
        await Match(id=match_id).create(data)

    @staticmethod
    async def set_status(match_id: str, new_status: str):
        await Match(id=match_id).edit(column='status', value=new_status)

    async def get_matches(self, **kwargs) -> list[Any]:
        query = super()._qm.read('matches', columns='id')
        if kwargs:
            query = super()._qm.read('matches', columns='id',
                                     **kwargs)

        async with super()._database as db:
            return [
                x
                for row in await db.get_all(query)
                for x in row
            ]

    async def get_user_matches(self, user_id: str | int):
        return await self.get_matches(id=F"LIKE '%{user_id}%'")
