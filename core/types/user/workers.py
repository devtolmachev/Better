import asyncio
from typing import Any

from core.strategies import Strategies as Strategies
from core.types._base import BaseType as BaseType, BaseStrategy as BaseStrategy
from core.types.matches import Match
from core.types.user import User
from core.types.user.database import Counters as Counters, Urls as Urls
from core.types.user.tmp import TMP as TMP


class Worker(BaseType):
    __tablename__ = 'workers'
    __columns_required = ['token', 'user_id', 'id']

    def __init__(self, id: str | int):
        self.__id = id
        if str(id).count(':'):
            self.__id = id.split(':')[0]

    async def edit(
            self,
            columns: Any,
            values: Any
    ) -> None:
        async with super()._database as db:
            query = super()._qm.update(
                self.__tablename__,
                columns=columns,
                values=values,
                id=f"= '{self.id}'"
            )
            return await db.apply_query(query=query)

    async def create(
            self,
            user_id: str | int,
            token: str,
            worker_info: Any | None
    ) -> None:
        async with super()._database as db:
            columns = self.__columns_required.copy()
            columns.append('communication_chat')
            values = [token, user_id, self.id, user_id]

            if worker_info is not None:
                columns.append('worker_info')
                values.append(worker_info)

            query = super()._qm.create(
                self.__tablename__,
                columns=columns,
                values=values
            )
            return await db.apply_query(query=query)

    async def delete(self) -> None:
        token = await self.token
        user_id = await self.user_id
        await User(id=user_id).delete_worker(token)

        async with super()._database as db:
            query = super()._qm.delete(
                self.__tablename__,
                id=f"= '{self.id}'"
            )
            return await db.apply_query(query=query)

    @property
    async def user_id(self):
        async with super()._database as db:
            query = super()._qm.read(
                self.__tablename__,
                columns='user_id',
                id=f"= '{self.id}'"
            )
            return await db.get_one(query=query)

    async def update(
            self,
            columns: str | list,
            values: str | list,
            array: bool = False,
            **kwargs
    ) -> None:
        async with super()._database as db:
            query = super()._qm.update(
                self.__tablename__,
                columns=columns,
                values=values,
                array=array,
                **kwargs
            )
            return await db.apply_query(query=query)

    async def set_scanning_status(self, status: bool) -> None:
        async with super()._database as db:
            query = super()._qm.update(
                self.__tablename__,
                columns=['scanning'],
                values=[status],
                id=f"= '{self.id}'"
            )
            return await db.apply_query(query=query)

    @property
    async def get_scanning_status(self) -> bool:
        query = super()._qm.read(
            self.__tablename__,
            columns=['scanning'],
            id=f"= '{self.id}'"
        )
        async with super()._database as db:
            return await db.get_one(query=query)

    @property
    async def token(self) -> str:
        async with super()._database as db:
            query = super()._qm.read(
                self.__tablename__,
                columns='token',
                id=f"= '{self.id}'"
            )
            return await db.get_one(query=query)

    @property
    def id(self) -> str | int:
        return self.__id

    async def reset_worker(self):
        counters = await self.counter
        strategy = await self.strategy
        filters = strategy.filters

        [
            await counters.change_counter(
                bookmaker=await self.bookmaker,
                sport=await self.sport,
                strategy=strategy.name,
                coincidences=['guess', 'not_guess'],
                liga=liga,
                value=0
            )
            for liga in strategy._filters_dict["searching"]
        ]

        await self.urls.delete()
        [await Match(match_id).delete() for match_id in await self.matches()]

        await self.edit('filters', '{}')
        await self.edit('tmp_messages', '{}')
        await self.edit('info_matches', '{}')

        return await self.edit(columns='filters', values=filters)

    @property
    async def bookmaker(self) -> str:
        async with super()._database as db:
            query = super()._qm.read(
                self.__tablename__,
                columns='bookmaker',
                id=f"= '{self.id}'"
            )
            return await db.get_one(query=query)

    @property
    async def username(self) -> str:
        async with super()._database as db:
            query = super()._qm_jsonb.read(
                self.__tablename__,
                columns='worker_info',
                path=['username'],
                id=f"= '{self.id}'"
            )
            return await db.get_one(query=query)

    @property
    async def sport(self) -> str:
        async with super()._database as db:
            query = super()._qm.read(
                self.__tablename__,
                columns='sport',
                id=f"= '{self.id}'"
            )
            return await db.get_one(query=query)

    @property
    async def strategy(self) -> BaseStrategy:
        async with super()._database as db:
            q = super()._qm.read(
                self.__tablename__,
                columns='strategy',
                id=f"= '{self.id}'"
            )
            strategy = await db.get_one(query=q)

        return Strategies().get_strategy_by_name(
            name_strategy=strategy
        )

    @property
    async def worker_info(self) -> dict | str:
        async with super()._database as db:
            query = super()._qm_jsonb.read(
                self.__tablename__,
                columns='worker_info',
                id=f"= '{self.id}'"
            )
            return await db.get_one(query=query)

    @property
    async def counter(self) -> Counters:
        strategy = await self.strategy
        return Counters(
            id=self.id,
            strategy=strategy.name
        )

    @property
    def urls(self) -> Urls:
        return Urls(id=self.id)

    @property
    async def last_update(self) -> float:
        async with super()._database as db:
            query = super()._qm.read(
                self.__tablename__,
                columns='last_update',
                id=f"= '{self.id}'"
            )
            return float(await db.get_one(query=query))

    async def update_time(self) -> None:
        async with super()._database as db:
            query = super()._qm.update(
                self.__tablename__,
                columns='last_update',
                id=f"= '{self.id}'"
            )
            return await db.apply_query(query=query)

    async def matches(self, table: str = 'matches') -> list[str]:
        async with super()._database as db:
            query = super()._qm.read(
                table,
                columns='id',
                id=f"LIKE '%{self.id}%'"
            )

            data = [
                match_id
                for row in await db.get_all(query=query)
                for match_id in row
            ]

            return data

    async def is_validate_counter(
            self,
            type_coincidence: str,
            filtering: str
    ) -> bool:
        async with super()._database as db:
            strategy_query = super()._qm.read(
                self.__tablename__,
                columns='strategy',
                id=f"= '{self.id}'"
            )

            counter_query = super()._qm_jsonb.read(
                self.__tablename__,
                columns='counters',
                path=['fonbet', 'basketball',
                      await db.get_one(query=strategy_query),
                      filtering,
                      type_coincidence],
                id=f"= '{self.id}'"
            )
            settings_query = super()._qm_jsonb.read(
                self.__tablename__,
                columns='settings',
                path=['fonbet',
                      'basketball',
                      await db.get_one(query=strategy_query),
                      filtering,
                      'max_counter'],
                id=f"= '{self.id}'"
            )

            counter = int(await db.get_one(query=counter_query))
            settings = int(await db.get_one(query=settings_query))

            return counter >= settings

    async def get(self, column: str | str) -> Any:
        async with super()._database as db:
            query = super()._qm.read(
                self.__tablename__,
                columns=column,
                id=f"= '{self.id}'"
            )
            return await db.get_one(query=query)

    async def get_counter(
            self,
            filtering: str,
            type_coincidence: str,
            bookmaker: str = 'fonbet',
            sport: str = 'basketball'
    ) -> int:
        async with super()._database as db:
            strategy = await self.strategy
            query = super()._qm_jsonb.read(
                self.__tablename__,
                columns='counters',
                path=[bookmaker,
                      sport,
                      strategy.name,
                      filtering,
                      type_coincidence],
                id=f"= '{self.id}'"
            )
            counter = await db.get_one(query=query)
            return int(counter)

    @property
    def tmp(self) -> TMP:
        return TMP(id=self.id)

    @property
    async def filters(self) -> dict[str, [list[str]]]:
        async with super()._database as db:
            query = super()._qm.read(
                self.__tablename__,
                columns='filters',
                id=f"= '{self.id}'"
            )
            return await db.get_one(query=query)

    @property
    async def what_search(self) -> dict[str, list[str]] | dict[None]:
        filters = await self.filters

        if filters is None or not filters.get("searching"):
            return {}

        filters = filters.get("searching")
        urls_filters = [
            filtering
            for url, filtering in await self.urls.get()
        ]

        what_search = [
            x
            for x in filters + urls_filters
            if x not in urls_filters
        ]

        user_filter = await self.filters
        user_filter["black_id"] = []
        user_filter["searching"] = what_search
        return user_filter

    @property
    async def bets_statistic(self) -> dict:
        async with super()._database as db:
            query = super()._qm.read(
                self.__tablename__,
                columns='bet_statistic',
                id=f"= '{self.id}'"
            )
            return await db.get_one(query=query)

    @property
    async def chat(self) -> int | str:
        async with super()._database as db:
            query = super()._qm.read(
                self.__tablename__,
                columns='communication_chat',
                id=f"= '{self.id}'"
            )

            return await db.get_one(query=query)


async def main():
    w = Worker("6243335297")
    print(await w.chat)


if __name__ == '__main__':
    asyncio.run(main())
