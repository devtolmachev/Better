import json
import time
from typing import Any, Tuple, List

import psycopg2

import etc.database
from utils.exceptions import NotFoundError


class Database:
    """A base class for database"""
    __instance = None
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
                            "max_counter": "10"
                        },
                        "NBA 2K23": {
                            "max_counter": "10"
                        }
                    },
                    "scenarios": {
                        "NBA 2K23": {
                            "max_counter": "1"
                        }
                    }
                }
            }
        }
    )

    def __init__(self):
        self.__connect()

    def __connect(self):
        base = psycopg2.connect(
            database=etc.database.database,
            host=etc.database.host,
            user=etc.database.user,
            password=etc.database.password
        )

        self.base = base
        self.cursor = base.cursor()
        base.autocommit = True

        if base:
            self.create_tables()

    def create_tables(self):
        with self.base.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS users("
                        "user_id VARCHAR(50) NOT NULL PRIMARY KEY,"
                        "username VARCHAR(50),"
                        "settings JSONB NOT NULL DEFAULT '%s',"
                        "counters JSONB NOT NULL DEFAULT '%s',"
                        "scanning BOOLEAN NOT NULL DEFAULT false,"
                        "filters JSONB,"
                        "urls TEXT[] NOT NULL DEFAULT '{}',"
                        "tmp_messages JSONB NOT NULL DEFAULT '{}',"
                        "strategy VARCHAR(100),"
                        "info_matches JSONB NOT NULL DEFAULT '{}')" % (self.settings_column,
                                                                       self.counter_column))

            cur.execute("CREATE TABLE IF NOT EXISTS matches("
                        "id VARCHAR(150) NOT NULL PRIMARY KEY,"
                        "username VARCHAR(100), "
                        "timer VARCHAR(20), "
                        "team1 VARCHAR(300), "
                        "team2 VARCHAR(300),"
                        "part VARCHAR(10), "
                        "status VARCHAR(20) DEFAULT 'playing', "
                        "scores JSONB NOT NULL DEFAULT '{}',"
                        "prognoses JSONB NOT NULL DEFAULT '{}',"
                        "filter VARCHAR(100),"
                        "json_url VARCHAR(500))")

            cur.execute("CREATE TABLE IF NOT EXISTS cache("
                        "user_id VARCHAR(50) NOT NULL PRIMARY KEY,"
                        "bot_username VARCHAR(50),"
                        "first_match_session JSONB NOT NULL DEFAULT '{}',"
                        "last_match_session JSONB NOT NULL DEFAULT '{}',"
                        "startup_session NUMERIC DEFAULT EXTRACT(epoch FROM now()))")

    def close_connection(self):
        self.base.close()

    def get_one(self, query: Any) -> list | str | dict | int:
        with self.base.cursor() as cur:
            try:
                cur.execute(query=query)
                return cur.fetchall()[0][0]
            except (psycopg2.ProgrammingError, psycopg2.errors.UniqueViolation):
                pass
            except IndexError:
                raise NotFoundError

    def get_more(self, query: Any) -> tuple[Any, ...]:
        with self.base.cursor() as cur:
            try:
                cur.execute(query=query)
                return cur.fetchall()[0]
            except (psycopg2.ProgrammingError, psycopg2.errors.UniqueViolation):
                pass
            except IndexError:
                raise NotFoundError

    def get_all(self, query: Any) -> list[tuple[Any, ...]]:
        with self.base.cursor() as cur:
            try:
                cur.execute(query=query)
                return cur.fetchall()
            except (psycopg2.ProgrammingError, psycopg2.errors.UniqueViolation):
                pass
            except IndexError:
                raise NotFoundError

    def apply_query(self, query: Any) -> None:
        try:
            with self.base.cursor() as cur:
                cur.execute(query=query)
        except psycopg2.errors.UniqueViolation:
            pass

    def __enter__(self):
        self.__init__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()
