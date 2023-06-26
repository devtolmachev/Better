import asyncio
import json
from typing import Any

import asyncpg
from asyncpg import Record, Connection, Pool

import etc.database
from utils.exceptions import NotFoundError


def val_json(data: str):
    try:
        json.loads(data)
    except (ValueError, TypeError):
        return False

    return True


class Database:
    """A base class for database"""
    __attrs_pool = None
    pool: Pool | None = None
    counter_column = json.dumps(
        {
            "fonbet": {
                "basketball": {
                    "random": {
                        "": {
                            "guess": "0",
                            "not_guess": "0"
                        },
                        "NBA 2K23": {
                            "guess": "0",
                            "not_guess": "0"
                        }
                    },
                    "scenarios": {
                        "NBA 2K23": {
                            "guess": "0",
                            "not_guess": "0"
                        },
                        "temp_counters": {
                            "guess": "0",
                            "not_guess": '0'
                        }
                    }
                }
            }
        }
    )

    settings_column = json.dumps(
        {
            "fonbet": {
                "basketball": {
                    "random": {
                        "": {
                            "max_counter": "0"
                        },
                        "NBA 2K23": {
                            "max_counter": "0"
                        }
                    },
                    "scenarios": {
                        "NBA 2K23": {
                            "max_counter": "0"
                        }
                    }
                }
            }
        }
    )

    @classmethod
    def __init__(cls):
        pass

    @classmethod
    async def create_connection(cls):
        if cls.pool is None:
            cls.pool: Connection = await asyncpg.create_pool(
                database=etc.database.database,
                user=etc.database.user,
                password=etc.database.password,
                host=etc.database.host
            )

        await cls.create_tables()

    @classmethod
    async def create_tables(cls):
        async with cls.pool.acquire() as pool:
            pool: Pool

            await pool.execute(
                "CREATE TABLE IF NOT EXISTS users("
                "id VARCHAR(150) NOT NULL PRIMARY KEY,"
                "username VARCHAR(150) NOT NULL,"
                "info_profile JSONB DEFAULT '{}',"
                "workers JSONB DEFAULT '{}')"
            )

            await pool.execute(
                "CREATE TABLE IF NOT EXISTS matches("
                "id VARCHAR(150) NOT NULL PRIMARY KEY,"
                "timer VARCHAR(20), "
                "team1 VARCHAR(300), "
                "team2 VARCHAR(300),"
                "part VARCHAR(10), "
                "status VARCHAR(20) DEFAULT 'playing', "
                "scores JSONB NOT NULL DEFAULT '{}',"
                "prognoses JSONB NOT NULL DEFAULT '{}',"
                "filter VARCHAR(100),"
                "json_url VARCHAR(500))"
            )

            await pool.execute(
                "CREATE TABLE IF NOT EXISTS workers("
                "id VARCHAR(50) NOT NULL PRIMARY KEY,"
                "token VARCHAR(150) NOT NULL UNIQUE, "
                "user_id VARCHAR(50) NOT NULL, "
                "worker_info JSONB DEFAULT '{}', "
                "scanning BOOLEAN NOT NULL DEFAULT false,"
                "settings JSONB NOT NULL DEFAULT '%s',"
                "counters JSONB NOT NULL DEFAULT '%s',"
                "filters JSONB NOT NULL DEFAULT '{}',"
                "urls TEXT[] NOT NULL DEFAULT '{}',"
                "tmp_messages JSONB NOT NULL DEFAULT '{}',"
                "strategy VARCHAR(100),"
                "info_matches JSONB NOT NULL DEFAULT '{}', "
                "bookmaker VARCHAR(300) NOT NULL DEFAULT 'fonbet',"
                """
                bet_statistic JSONB NOT NULL DEFAULT 
                '{"failed": 0, "success": 0}', 
                """
                "sport VARCHAR(150) NOT NULL DEFAULT 'basketball')" %
                (
                    cls.settings_column,
                    cls.counter_column
                )
            )

            await pool.execute(
                "CREATE TABLE IF NOT EXISTS sports("
                "name VARCHAR(100) NOT NULL, "
                "leagues JSONB NOT NULL DEFAULT '{}', "
                "parameters JSONB DEFAULT '{}')"
            )

    @classmethod
    async def close_connection(cls):
        if cls.pool is not None:
            await cls.pool.close()
            cls.pool = None

    @classmethod
    async def get_one(cls, query: str) -> Any:
        async with cls.pool.acquire() as pool:
            try:
                result = await pool.fetchval(query=query)
            except AttributeError:
                return []
            except IndexError:
                await cls.__data_table(query=query)

        return json.loads(result) if val_json(result) else result

    @classmethod
    async def get_more(cls, query: str) -> list[Any]:
        async with cls.pool.acquire() as pool:
            try:
                records = await pool.fetchrow(query=query)
                result = records.values()
            except AttributeError:
                return []
            except IndexError:
                await cls.__data_table(query=query)

        return [
            json.loads(x)
            if val_json(x) is True
            else x

            for x in result
        ]

    @classmethod
    async def get_all(cls, query: str) -> list[list[Any]]:
        async with cls.pool.acquire() as pool:
            try:
                result: list[Record] = await pool.fetch(query=query)

                if not all(len(i) for i in result):
                    raise IndexError

            except IndexError:
                await cls.__data_table(query=query)

        return [
            [
                json.loads(value)
                if val_json(value) is True
                else value
                for value in row
            ]
            for row in result
        ]

    @classmethod
    async def __data_table(cls, query: str):
        data = 'Не удалось прочитать данные из таблицы'

        table = (
            query.lower().split('from ')[1].split()[0]
            if query.lower().startswith('select')
            else query.lower().split()[1]
            if query.lower().startswith('update')
            else query.lower().split()[2]
            if query.lower().startswith('insert')
            else "Unknown Table"
        )

        if not table.lower().count('unknown'):
            data = (
                await cls.get_all(query=f"SELECT * FROM {table}")
                if not table.lower().count("unknown")
                else table
            )

        raise NotFoundError(f"Wrong Query -> {query}\n"
                            f"Data Table -> {data}")

    @classmethod
    async def apply_query(cls, query: str) -> None:
        async with cls.pool.acquire() as pool:
            try:
                await pool.execute(query=query)
            except asyncpg.UniqueViolationError:
                pass

    @classmethod
    async def __aenter__(cls):
        await cls.create_connection()
        return cls

    @classmethod
    async def __aexit__(cls, exc_type, exc_val, exc_tb):
        await cls.close_connection()


async def main():
    import time
    async with Database() as db:
        query = "TRUNCATE TABLE users"
        await db.apply_query(query)
        quantity = 1_000
        print('Пошли запросы в БД')
        start = time.time()

        [
            await db.apply_query(
                f"INSERT INTO users(id, username) VALUES ('{i}', '{i}')"
            )

            for i in range(quantity)
        ]

        finished = f"{round(time.time() - start, 2)} секунд"
        print(f"Выполнено {quantity} вставок за {finished}!")


if __name__ == '__main__':
    asyncio.run(main())
