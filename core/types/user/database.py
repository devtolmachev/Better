from core.types._base import BaseType


class Counters(BaseType):
    """
    Управление счетчиками ботов
    """
    __table = 'workers'

    def __init__(self,
                 id: str | int,
                 strategy: str):
        self.__id = id
        self.__strategy = strategy

    async def get_counter(
            self,
            filtering: str,
            type_coincidence: str,
            bookmaker: str = 'fonbet',
            sport: str = 'basketball'
    ) -> int:
        strategy = self.__strategy

        query = super()._qm_jsonb.read(
            self.__table,
            columns='counters',
            path=[bookmaker,
                  sport,
                  strategy,
                  filtering,
                  type_coincidence],
            id=f"= '{self.__id}'"
        )
        async with super()._database as db:
            counter = await db.get_one(query=query)
            return int(counter)

    async def get_counters(
            self,
            bookmaker: str = 'fonbet',
            sport: str = 'basketball'
    ):
        query = super()._qm_jsonb.read(
            self.__table,
            columns='counters',
            path=[bookmaker, sport, self.__strategy]
        )
        async with super()._database as db:
            counters: dict = await db.get_one(query=query)
            return counters

    async def get_max_counter(
            self,
            bookmaker: str,
            sport: str,
            strategy: str = None
    ) -> dict:
        strategy = self.__strategy if not strategy else strategy

        query_for_leagues = super()._qm_jsonb.read(
            self.__table,
            columns='settings',
            path=[bookmaker, sport, strategy],
            id=f"= '{self.__id}'"
        )

        async with super()._database as db:
            data = {
                liga: await db.get_one(
                    query=super(Counters, self)._qm_jsonb.read(
                        self.__table,
                        columns='settings',
                        path=[bookmaker,
                              sport,
                              strategy,
                              liga,
                              'max_counter'],
                        id=f"= '{self.__id}'"
                    )
                )

                for liga in (await db.get_one(
                    query=query_for_leagues
                )).keys()
            }

        return data

    async def change_counter(self,
                             bookmaker: str,
                             strategy: str,
                             sport: str,
                             liga: str,
                             coincidences: list,
                             value: str | int):
        async with super()._database as db:
            return [
                await db.apply_query(
                    query=super(Counters, self)._qm_jsonb.update(
                        self.__table,
                        columns='counters',
                        path=[bookmaker, sport, strategy, liga, coincidence],
                        values=value
                    )
                )

                for coincidence in coincidences
            ]

    async def change_max_counter(
            self,
            bookmaker: str,
            strategy: str,
            sport: str,
            liga: str,
            value: str | int
    ) -> None:
        query = super()._qm_jsonb.update(
            self.__table,
            columns='settings',
            path=[bookmaker, sport, strategy, liga, "max_counter"],
            values=value
        )

        async with super()._database as db:
            return await db.apply_query(query=query)


class Urls(BaseType):
    """
    Управление ссылками на отслеживание матчей
    """
    __table = 'workers'

    def __init__(self, id: str | int):
        self.__id = id

    async def append(self, url: list) -> None:
        """
        Добавить url в базу
        :param url: Url должен содержать ссылку на отслеживание - и фильтр с
            которым был найден матч
        :type url: list
        """
        query = super()._qm.unite(
            self.__table, columns='urls', values=url,
            id=f"= '{self.__id}'"
        )
        async with super()._database as db:
            return await db.apply_query(query=query)

    async def get(self) -> list[list[str, str]] | list:
        """
        Получить url пользователя
        :return: Возвращает Url сканированных матчей пользователя
        :rtype: list
        """

        async with super()._database as db:
            query = super()._qm.read(
                self.__table, columns='urls',
                id=f"= '{self.__id}'"
            )

            result = await db.get_one(query=query)
            if not result:
                result = []

            return result

    async def delete(self, url: list | str = None):
        """
        Удалить url пользователя
        :param url: Список с ссылкой на отслеживание
        :type url: list
        """
        async with super()._database as db:
            query = super()._qm.read(
                self.__table,
                columns='urls',
                id=f"= '{self.__id}'"
            )

            urls: list | str = await db.get_one(query=query)

            array = True
            if not urls or not url:
                array = False
                urls = '{}'

            else:
                urls.remove(url)
                if not urls:
                    array = False
                    urls = '{}'

            if array:
                query_update = super()._qm_array.update(
                    self.__table,
                    columns='urls',
                    values=urls,
                    wrappers=1,
                    id=f"= '{self.__id}'",
                )

            else:
                query_update = super()._qm.update(
                    self.__table,
                    columns='urls',
                    values=urls,
                    id=f"= '{self.__id}'"
                )

            return await db.apply_query(query=query_update)


class Settings(BaseType):
    __table = 'workers'

    def __init__(self, id: str | int):
        self.__id = id
