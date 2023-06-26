import datetime
import time
from typing import Any

import utils.exceptions
from core.types._base import BaseType as BaseType


class User(BaseType):
    __table__ = 'users'

    def __init__(self, id: str | int):
        self.__id = id

    async def save(
            self,
            username: str
    ) -> None:

        async with super()._database as db:
            query = super()._qm.create(
                self.__table__,
                columns=['id', 'username'],
                values=[self.__id, username]
            )
            return await db.apply_query(query=query)

    async def delete(
            self
    ) -> None:

        async with super()._database as db:
            query = super()._qm.delete(
                self.__table__,
                id=f"= '{self.id}'"
            )
            return await db.apply_query(query=query)

    async def edit(
            self,
            column: str,
            value: Any
    ) -> None:

        async with super()._database as db:
            query = super()._qm.update(
                self.__table__,
                columns=[column], values=[value],
                id=f"= '{self.id}'"
            )

            return await db.apply_query(query=query)

    async def add_value(
            self,
            columns: str | list,
            values: str | list,
            **kwargs
    ) -> None:

        async with super()._database as db:
            arrays = 2
            if kwargs["arrays"] is not None:
                arrays = kwargs["arrays"]

            query = super()._qm.unite(
                self.__table__,
                columns=columns,
                values=values,
                arrays=arrays
            )

            return await db.apply_query(query=query)

    async def matches(
            self,
            table: str = 'matches'
    ) -> list:

        async with super()._database as db:
            query = super()._qm.read(
                table, columns='id',
                id=f"LIKE '%{self.id}%'"
            )

            data = [
                id
                for row in await db.get_all(query=query)
                for id in row
            ]

            return data

    async def get(
            self, column: str
    ) -> Any:

        async with super()._database as db:
            query = super()._qm.read(
                'users', columns=column,
                id=f"= '{self.id}'"
            )

            return await db.get_one(query=query)

    @property
    def id(self) -> str | int:
        return self.__id

    @property
    async def register_time(
            self
    ) -> datetime.time | int:

        async with super()._database as db:
            query = super()._qm_jsonb.read(
                self.__table__, columns='info_profile',
                path=['register'],
                id=f"= '{self.id}'"
            )

            return await db.get_one(query=query)

    async def set_register_time(
            self
    ) -> None:

        async with super()._database as db:
            query = super()._qm_jsonb.update(
                self.__table__,
                columns='info_profile',
                path=['register'],
                values=int(time.time()),
                id=f"= '{self.id}'"
            )

            return await db.apply_query(query=query)

    @property
    async def username(
            self
    ) -> str:

        async with super()._database as db:
            query = super()._qm.read(
                'users', columns='username',
                id=f"= '{self.id}'"
            )
            return await db.get_one(query=query)

    async def get_workers(
            self
    ) -> list:

        async with super()._database as db:
            query = super()._qm.read(
                self.__table__,
                columns='workers',
                id=f"= '{self.id}'"
            )

            try:
                return await db.get_one(query=query)
            except utils.exceptions.NotFoundError:
                return []

    async def rename_id_worker(
            self,
            old_data,
            new_data
    ) -> None:

        data = (await self.get_workers())[old_data]

        q1 = super()._qm_jsonb.delete_key(
            self.__table__,
            columns='workers',
            key=old_data,
            id=f"= '{self.id}'"
        )
        q2 = super()._qm_jsonb.update(
            self.__table__,
            columns='workers',
            path=[new_data],
            values=data,
            add_key=True
        )

        async with super()._database as db:
            [
                await db.apply_query(query=query)
                for query in [q1, q2]
            ]
            return

    async def add_worker(self, token: str):
        async with super()._database as db:
            return await db.apply_query(
                query=super()._qm_jsonb.update(
                    self.__table__,
                    columns='workers',
                    values=f"register {datetime.datetime.now()}",
                    path=[token],
                    add_key=True,
                    id=f"= '{self.id}'"
                )
            )

    async def delete_worker(
            self,
            token: str | int | Any
    ) -> None:

        async with super()._database as db:
            query = super()._qm_jsonb.delete_key(
                self.__table__,
                columns='workers',
                key=token
            )

            return await db.apply_query(query=query)
