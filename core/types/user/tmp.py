import asyncio
import json

from core.types._base import BaseType
from core.types.matches.match import Match
from core.types.matches.scores import Scores


class Events(BaseType):
    """
    Класс управляющий ивентами
    """

    __table = 'workers'

    def __init__(self, id: str | int):
        self.__id = id

    async def get_event(self, filtering: str) -> list[str] | list:
        """
        Получить ивент по фильтру
        :param filtering: Фильтр по которому был отобран матч
        :type filtering: str
        :return: Список с текстами не дошедших ивентов до пользователя
        :rtype: list[str]
        """
        async with super()._database as db:

            query = super()._qm_jsonb.read(
                self.__table,
                columns='tmp_messages',
                path=[filtering],
                id=f"= '{self.__id}'"
            )

            tmp_messages = await db.get_one(query=query)

            try:
                return list(filter(None, tmp_messages))
            except TypeError:
                return []

    async def set_event(self, message: str, filtering: str) -> None:
        """
        Позволяет установить ивент матча
        :param message: Текст будущего ивента
        :type message: str
        :param filtering:  Фильтр по которому был отобран матч
        :type filtering: str
        """
        isnull = not await self.get_event(filtering=filtering)

        if isnull is True:
            query = super()._qm_jsonb.update(
                self.__table,
                columns='tmp_messages',
                path=[filtering],
                values=message, array=True,
                id=f"= '{self.__id}'"
            )

        else:
            query = super()._qm_jsonb.unite(
                self.__table,
                columns='tmp_messages',
                path=[filtering],
                values=message, array=True,
                id=f"= '{self.__id}'"
            )

        async with super()._database as db:
            return await db.apply_query(query=query)

    async def delete_event(self, filtering: str = None) -> None:
        """
        Удаляет ивент по фильтру
        :param filtering: Фильтр по которому был отобран матч
        :type filtering: str
        """
        async with super()._database as db:

            if filtering is None:
                query = super()._qm.update(
                    self.__table,
                    columns=['tmp_messages'],
                    values=['{}'],
                    id=f"= '{self.__id}'"
                )
            else:
                query = super()._qm_jsonb.delete_key(
                    self.__table,
                    columns="tmp_messages",
                    key=filtering
                )
            return await db.apply_query(query=query)


class Infos(BaseType):
    """
    Класс управляющий кэшированием данных о матчах
    """

    def __init__(self, id: str | int, table_name: str = 'cache'):
        self.__id = id
        self.__table = table_name

    async def set_infos(self, match_id: str) -> None:
        async with super()._database as db:
            match = Match(id=match_id)

            query = super()._qm.read(
                'matches',
                columns='scores',
                id=f"= '{match_id}'"
            )
            scores = await db.get_one(query=query)

            prognoses_query = super()._qm.read(
                'matches', columns='prognoses',
                id=f"= '{match_id}'"
            )
            prognoses = await db.get_one(
                query=prognoses_query
            )

            create_query = super()._qm.create(
                self.__table,
                columns=['id',
                         'scores',
                         'prognoses'],
                values=[match_id,
                        json.dumps(scores),
                        json.dumps(prognoses)]
            )

            await db.apply_query(query=create_query)

            teams = f"<b>{match.teams}</b>"
            scores = Scores(scores=scores).format_score_fonbet()
            prognoses = match.bets.all_bets
            query = super()._qm_jsonb.update(
                'users', columns='info_matches',
                values=f"{teams}${scores}${prognoses}",
                path=[match_id],
                id=f"= '{self.__id}'"
            )

            await db.apply_query(query=query)

    async def get_infos(self, match_id: str) -> str:
        async with super()._database as db:
            query = super()._qm_jsonb.read(
                'users', columns='info_matches',
                path=[match_id],
                id=f"= '{self.__id}'"
            )

            infos_text = '\n'.join(
                await db.get_one(
                    query=query
                ).split('$')
            )

            return infos_text


class TMP(BaseType):
    """
    Класс выдающий доступ к временным объектам
    """

    def __init__(self, id: str | int):
        self.__id = id

    @property
    def events(self):
        return Events(id=self.__id)

    @property
    def infos(self):
        return Infos(id=self.__id)
