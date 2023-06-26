from typing import Any, Collection

from utils.exceptions import WrongQueryError


class QMService:
    """
    Query Maker Service
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def truncate(**kwargs) -> str:
        """
        Формирует запрос TRUNCATE
        :param kwargs: Должен быть один именованный параметр, название
            которого = что нужно очистить (table), а значение =
            названию этого объекта (param: table=users)
        :return: Строковый запрос в базу данных
        :rtype: str
        """
        if len(kwargs) > 1:
            raise WrongQueryError('Должен быть только один параметр')

        obj = ''.join(kwargs.keys())
        value = ''.join(kwargs.values())

        query = "TRUNCATE %s %s" % (obj, value)
        return query

    @staticmethod
    def create(table: str, *,
               values: Collection,
               columns: Collection = '') -> str:
        """
        Формирует запрос INSERT
        :param table: Название таблицы
        :type table: str
        :param columns: Название столбцов таблицы, можно не указывать -
            тогда будет вставка по всей таблице
        :type columns: list | tuple
        :param values: Значения которые нужно вставить в таблицу.
            По стандарту значения должны быть в объекте, по которому можно
            итерироваться
        :type values: list | tuple
        :return:
        :rtype:
        """
        if hasattr(columns, '__iter__') and hasattr(values, '__iter__') and \
                len(columns) != len(values) and columns != '':
            raise WrongQueryError(f"{values=} {columns=}")

        if columns == '':
            columns_ = columns
        else:
            columns_ = f"({', '.join(columns)})"

        if type(values) == str:
            values_ = values
        else:
            values_ = f"""VALUES ('{"', '".join(
                list(map(lambda x: str(x), values)))}')"""

        query = "INSERT INTO %s%s %s;" % (table, columns_, values_)
        return query

    def read(self, table: str, *,
             columns: Collection | str,
             **kwargs) -> str:
        """
        Формирует запрос SELECT
        :param table: Название таблицы
        :type table: Any
        :param columns: Название столбца
        :type columns: str
        :param kwargs: Условие WHERE. Пример - user_id="LIKE '2027%'"
        :return: SQL Запрос SELECT
        :rtype: str
        """

        where = []
        if type(columns) == str:
            columns = [columns]
        if kwargs:
            for k, v in kwargs.items():

                if not where:
                    where.append(f"WHERE {k} {v}")
                else:
                    where.append(f"AND {k} {v}")

        query = """SELECT %s FROM %s %s;""" % (', '.join(columns),
                                               table,
                                               ' '.join(where))
        return query

    @staticmethod
    def unite(table: str, *,
              columns: str,
              values: list | Any,
              arrays: int = 2,
              **kwargs: str) -> str:
        """
        Формирует вопрос для соединения/объединения/добавления элементов
        :param arrays:
        :type arrays:
        :param table: Название таблицы
        :type table: Any
        :param columns: Название столбца
        :type columns: str
        :param values: Значение
        :type values:  list | Any
        :param kwargs: Условие WHERE. Пример - user_id="LIKE '2027%'"
        :return: SQL Запрос для соединения/объединения/добавления элементов
        :rtype: str
        """

        if isinstance(values, list):
            values = f'''"{'", "'.join(values)}"'''
            values = f"'{arrays * '{'}%s{arrays * '}'}'" % values

        where = []
        if kwargs:
            for k, v in kwargs.items():
                if not where:
                    where.append(f"WHERE {k} {v}")
                else:
                    where.append(f"AND {k} {v}")

        where = ' '.join(where)

        query = """UPDATE %s SET %s = %s || %s %s;""" % (table,
                                                         columns,
                                                         columns,
                                                         values,
                                                         where)

        return query

    @staticmethod
    def update(table: str, *,
               columns: Collection[str] | str,
               values: Collection[str],
               array: bool = False,
               **kwargs: str) -> str:
        """
        Формирует SQL запрос UPDATE
        :param table: Название таблицы
        :type table: Any
        :param columns: Название столбца (ов)
        :type columns: str
        :param values: Значение (я)
        :type values:  list | Any
        :param array: Нужно ли использовать тип данных МАССИВ
        :type array: bool
        :param kwargs: Условие WHERE. Пример - user_id="LIKE '2027%'"
        :return: SQL запрос UPDATE
        :rtype: str
        """
        update = []
        where = []

        if isinstance(columns, str):
            columns = [columns]
        if isinstance(values, str):
            values = [values]

        if kwargs:
            for k, v in kwargs.items():
                if not where:
                    where.append(f"WHERE {k} {v}")
                else:
                    where.append(f"AND {k} {v}")

        for column, value in zip(columns, values):
            update_query = "%s = '%s', " % (column, value)
            if array:
                update_query = "%s = ARRAY['%s']::text[], " % (column, value)
            update.append(update_query)

        query = "UPDATE %s SET %s %s;" % (table,
                                          '\n'.join(update)[:-2],
                                          ' '.join(where))

        return query

    @staticmethod
    def delete(table: str, **kwargs: str):
        """
        Формирует SQL запрос DELETE FROM
        :param table: Название таблицы
        :type table: str
        :param kwargs: Условие WHERE. Пример - user_id="LIKE '2027%'"
        :return: SQL запрос DELETE FROM
        :rtype: str
        """
        where = []
        if kwargs:
            for k, v in kwargs.items():
                if not where:
                    where.append(f"WHERE {k} {v}")
                else:
                    where.append(f"AND {k} {v}")
        return """DELETE FROM %s %s;""" % (table, ' '.join(where))


class ArrayQMService:
    """
    Array Query Maker Service
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def update(table,
               *,
               columns: Collection[str] | str,
               values: Collection[str] | str,
               sql_type: Any = '',
               sql_custom_type: Any = None,
               wrappers: int = 1,
               **kwargs):
        """
        Формирует запрос ARRAY UPDATE

        :param table: Название Таблицы
        :type table: str
        :param columns: Название Столбцов. Можно передать одно, а можно
            несколько
        :type columns: str | list | tuple
        :param values: Значения на которые можно обновить
        :type values: str | list | tuple
        :param sql_type: Параметр служит для преобразования python типа в тип
            sql. Например, вы передаете строку ('str'), а запрос сформируется в
            вид UPDATE table SET column = ARRAY['str']::text[]
        :param sql_custom_type: Если такого типа нет в python, укажите его
            вручную в виде строки. Например sql_custom_type="::custom_type[]"
        :param wrappers: Сколько раз квадратные скобки должны обернуть ваше
            значение
        :type wrappers: int
        :param kwargs: Служит для формирования sql условия where
        :return: Сформированный sql array запрос
        :rtype: str
        """

        if isinstance(columns, str):
            columns = [columns]

        if isinstance(values, str):
            values = [values]

        # sql condition where
        where = []
        if kwargs:
            for k, v in kwargs.items():
                if not where:
                    where.append(f"WHERE {k} {v}")
                else:
                    where.append(f"AND {k} {v}")

        if isinstance(sql_type, str):
            sql_type = '::text[]'

        if sql_custom_type is not None:
            sql_type = sql_custom_type

        wrapper = '[]'
        if len(wrapper) % 2 != 0:
            raise NotImplementedError

        wrappers = wrappers - 1
        wrap_indexes = int(len(wrapper) / 2)
        wrap_1 = wrapper[wrap_indexes - 1]
        wrap_2 = wrapper[wrap_indexes]

        query = ("UPDATE %s SET %s = ARRAY%s%s %s;" %
                 (
                     table, ', '.join(columns),
                     f"{wrap_1 * wrappers}{values}{wrap_2 * wrappers}",
                     sql_type, ' '.join(where)
                 ))

        return query

    @staticmethod
    def create(table: str, *,
               values: Collection,
               columns: Collection = '') -> str:
        """
        Формирует запрос INSERT
        :param table: Название таблицы
        :type table: str
        :param columns: Название столбцов таблицы, можно не указывать -
            тогда будет вставка по всей таблице
        :type columns: list | tuple
        :param values: Значения которые нужно вставить в таблицу.
            По стандарту значения должны быть в объекте, по которому можно
            итерироваться
        :type values: list | tuple
        :return:
        :rtype:
        """
        if hasattr(columns, '__iter__') and hasattr(values, '__iter__') and \
                len(columns) != len(values) and columns != '':
            raise WrongQueryError

        if columns == '':
            columns_ = columns
        else:
            columns_ = f"({', '.join(columns)})"

        if type(values) == str:
            values_ = values
        else:
            values_ = f"""VALUES ('{"', '".join(
                list(map(lambda x: str(x), values)))}')"""

        query = "INSERT INTO %s%s %s;" % (table, columns_, values_)
        return query

    @staticmethod
    def read(table: str, *,
             columns: Collection | str,
             **kwargs) -> str:
        """
        Формирует запрос SELECT
        :param table: Название таблицы
        :type table: Any
        :param columns: Название столбца
        :type columns: str
        :param kwargs: Условие WHERE. Пример - user_id="LIKE '2027%'"
        :return: SQL Запрос SELECT
        :rtype: str
        """

        where = []
        if type(columns) == str:
            columns = [columns]
        if kwargs:
            for k, v in kwargs.items():

                if not where:
                    where.append(f"WHERE {k} {v}")
                else:
                    where.append(f"AND {k} {v}")

        query = """SELECT %s FROM %s %s;""" % (', '.join(columns),
                                               table,
                                               ' '.join(where))
        return query

    @staticmethod
    def unite(table: str, *,
              columns: str,
              values: list | Any,
              **kwargs: str) -> str:
        """
        Формирует вопрос для соединения/объединения/добавления элементов
        :param table: Название таблицы
        :type table: Any
        :param columns: Название столбца
        :type columns: str
        :param values: Значение
        :type values:  list | Any
        :param kwargs: Условие WHERE. Пример - user_id="LIKE '2027%'"
        :return: SQL Запрос для соединения/объединения/добавления элементов
        :rtype: str
        """

        if isinstance(values, list):
            values = f'''"{'", "'.join(values)}"'''
            values = "'{{%s}}'" % values

        where = []
        if kwargs:
            for k, v in kwargs.items():
                if not where:
                    where.append(f"WHERE {k} {v}")
                else:
                    where.append(f"AND {k} {v}")

        where = ' '.join(where)

        query = """UPDATE %s SET %s = %s || %s %s;""" % (table,
                                                         columns,
                                                         columns,
                                                         values,
                                                         where)

        return query

    @staticmethod
    def delete(table: str, **kwargs: str):
        """
        Формирует SQL запрос DELETE FROM
        :param table: Название таблицы
        :type table: str
        :param kwargs: Условие WHERE. Пример - user_id="LIKE '2027%'"
        :return: SQL запрос DELETE FROM
        :rtype: str
        """
        where = []
        if kwargs:
            for k, v in kwargs.items():
                if not where:
                    where.append(f"WHERE {k} {v}")
                else:
                    where.append(f"AND {k} {v}")
        return """DELETE FROM %s %s;""" % (table, ' '.join(where))


class JsonbQMService(QMService):
    """
    Jsonb Query Maker Service
    """

    @staticmethod
    def delete_key(table: str,
                   *,
                   columns: str,
                   key: Any,
                   **kwargs: str) -> str:
        """
        Формирует запрос UPDATE table SET column = column - key
        :param table: Название таблицы
        :type table: str
        :param columns: Название столбца
        :type columns: str
        :param key: Ключ который нужно удалить из Json поля
        :type key: str
        :param kwargs: Условие WHERE. Пример - user_id="LIKE '2027%'"
        :return: Sql Запрос в виде строки
        :rtype:str
        """

        where = []
        if kwargs:
            for k, v in kwargs.items():
                if not where:
                    where.append(f"WHERE {k} {v}")
                else:
                    where.append(f"AND {k} {v}")

        query = ("UPDATE %s SET %s = %s - '%s' %s;" %
                 (
                     table, columns, columns, key, " ".join(where))
                 )

        return query

    @staticmethod
    def update(table: str,
               *,
               columns: str,
               values: Any,
               path: list,
               add_key: bool = True,
               array: bool = False,
               **kwargs: str) -> str:
        """
        Формирует Jsonb SQL запрос UPDATE
        :param table: Название таблицы
        :type table: str
        :param columns: Название столбца
        :type columns: str
        :param values: Значение
        :type values:  list | Any
        :param path: Путь к значению
        :type path: list
        :param add_key: Если нет такого пути, создать и добавить значение?
        :type add_key: bool
        :param array: Нужно ли использовать тип данных МАССИВ
        :type array: bool
        :param kwargs: Условие WHERE. Пример - user_id="LIKE '2027%'"
        :return: SQL Запрос UPDATE для типа данных jsonb
        :rtype:str
        """
        where = []
        if kwargs:
            for k, v in kwargs.items():
                if not where:
                    where.append(f"WHERE {k} {v}")
                else:
                    where.append(f"AND {k} {v}")
        values = f'"{values}"'
        if array:
            values = f'[{values}]'

        query = ('''UPDATE %s SET %s = jsonb_set(%s, '{"%s"}', '%s', %s) %s;'''
                 % (
                     table,
                     columns,
                     columns,
                     '", "'.join(path),
                     values,
                     add_key,
                     ' '.join(where)
                 )
                 )

        return query

    @staticmethod
    def unite(table: str, *,
              columns: str,
              values: Any,
              path: list,
              array: bool = False,
              add_key: bool = True,
              **kwargs: str) -> str:
        """
        Формирует запрос для соединения/объединения/добавления элементов
        для типа данных jsonb
        :param table: Название таблицы
        :type table: str
        :param columns: Название столбца
        :type columns: str
        :param values: Значение
        :type values:  list | Any
        :param path: Путь к значению
        :type path: list
        :param add_key: Если нет такого пути, создать и добавить значение?
        :type add_key: bool
        :param array: Нужно ли использовать тип данных МАССИВ
        :type array: bool
        :param kwargs: Условие WHERE. Пример - user_id="LIKE '2027%'"
        :return: SQL Запрос соединения/объединения/добавления элементов
            для типа данных jsonb
        :rtype:str
        """
        where = []
        if kwargs:
            for k, v in kwargs.items():
                if not where:
                    where.append(f"WHERE {k} {v}")
                else:
                    where.append(f"AND {k} {v}")
        values = f'"{values}"'
        if array:
            values = f'[{values}]'

        query = (
                """UPDATE %s SET %s = jsonb_set(%s, '{"%s"}', 
                %s->'%s' || '%s', %s) %s;""" %
                (
                    table,
                    columns,
                    columns,
                    ", ".join(path),
                    columns,
                    "'->'".join(path),
                    values,
                    add_key,
                    ''.join(where)
                )
        )

        return query

    @staticmethod
    def read(table: str, *,
             columns: str,
             path: list = None,
             **kwargs) -> str:
        """
        Формирует SQL запрос SELECT
        :param table: Название таблицы
        :type table: str
        :param columns: Название столбца
        :type columns: str
        :param path: Путь к значению. Если указано None, то выборка будет по
            столбцу, исключая путь
        :type path: list
        :param kwargs: Условие WHERE. Пример - user_id="LIKE '2027%'"
        :return: SQL Запрос SELECT для типа данных jsonb
        :rtype:str
        """
        where = []

        if kwargs:
            for k, v in kwargs.items():
                if not where:
                    where.append(f"WHERE {k} {v}")
                else:
                    where.append(f"AND {k} {v}")

        src_path = ''
        if path:
            src_path = f"""->'{"'->'".join(path)}'"""

        query = """SELECT %s%s FROM %s %s;""" % (columns,
                                                 src_path,
                                                 table,
                                                 ' '.join(where))
        return query
