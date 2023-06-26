from typing import Any

import utils.exceptions
from core.types._base import BaseType
from core.types.matches.bet import Bet
from core.types.matches.scores import Scores


class Match(BaseType):
    """
    Управление матчами
    """

    def __init__(self, id: str | int):
        self.__match_id = id
        self.__table = 'matches'

    async def create(self, data: dict) -> None:
        async with super()._database as db:
            query = super()._qm.create(
                self.__table,
                columns=['id', "timer", "part", 'team1',
                         'team2', 'filter',
                         'json_url', 'scores',
                         'prognoses'],
                values=[self.id, data["timer"],
                        data["part"], data["team1"],
                        data["team2"], data['filter'],
                        data['json_url'],
                        data['scores'],
                        data['prognoses']]
            )
            return await db.apply_query(query=query)

    async def update(self, data: dict) -> None:
        async with super()._database as db:
            query = super()._qm.update(
                self.__table,
                columns=["timer", "part", 'scores'],
                values=[data["timer"], data["part"],
                        data['scores']],
                id=f"= '{self.id}'"
            )
            return await db.apply_query(query=query)

    async def delete(self) -> None:
        async with super()._database as db:
            query = super()._qm.delete(self.__table, id=f"= '{self.id}'")
            return await db.apply_query(query=query)

    async def edit(self, column: str, value: Any):
        async with super()._database as db:
            query = super()._qm.update(
                self.__table, columns=column,
                values=value,
                id=f"= '{self.id}'"
            )
            return await db.apply_query(query)

    @property
    async def teams(self) -> str:
        async with super()._database as db:
            query_team1 = super()._qm.read(self.__table, columns='team1',
                                           id=f"= '{self.id}'")

            query_team2 = super()._qm.read(self.__table, columns='team2',
                                           id=f"= '{self.id}'")

            team1 = await db.get_one(query_team1)
            team2 = await db.get_one(query_team2)
        return f'{team1} - {team2}'

    @property
    def id(self):
        return self.__match_id

    async def all(self):
        async with super()._database as db:
            query = super()._qm.read(
                self.__table, columns='*',
                id=f"= '{self.id}'"
            )

            return list(map(lambda x: str(x), await db.get_more(query)))

    @property
    async def timer(self):
        async with super()._database as db:
            query = super()._qm.read(
                self.__table, columns='timer',
                id=f"= '{self.id}'"
            )
            return await db.get_one(query=query)

    @property
    async def part(self) -> int:
        async with super()._database as db:
            query = super()._qm.read(
                self.__table,
                columns='part',
                id=f"= '{self.id}'"
            )

            return int(await db.get_one(query))

    @property
    async def status(self):
        async with super()._database as db:
            query = super()._qm.read(
                self.__table, columns='status',
                id=f"= '{self.id}'"
            )

            return await db.get_one(query)

    async def set_status(self, new_status: str):
        async with super()._database as db:
            query = super()._qm.update(
                'users', columns=['status'],
                values=new_status,
                id=f"= '{self.id}'"
            )

            return await db.apply_query(query=query)

    @property
    async def scores(self) -> Scores:
        async with super()._database as db:
            query = super()._qm.read(
                self.__table, columns='scores',
                id=f"= '{self.id}'"
            )

            return Scores(await db.get_one(query))

    @property
    def bets(self) -> Bet:
        return Bet(self.__match_id)

    @property
    async def filter(self) -> str:
        async with super()._database as db:
            query = super()._qm.read(
                self.__table, columns='filter',
                id=f"= '{self.id}'"
            )

            return await db.get_one(query)

    @property
    async def json_url(self) -> str:
        async with super()._database as db:
            query = super()._qm.read(
                self.__table, columns='json_url',
                id=f"= '{self.id}'"
            )

            return await db.get_one(query)

    @property
    async def in_database(self) -> bool:
        async with super()._database as db:
            query = super()._qm.read(
                self.__table, columns='id',
                id=f"= '{self.id}'"
            )
            try:
                result = await db.get_one(query)
                if result is None:
                    return False
                return True
            except utils.exceptions.NotFoundError:
                return False
