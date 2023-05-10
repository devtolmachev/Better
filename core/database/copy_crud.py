from typing import Any

from utils.exceptions import WrongQueryError


class CRUDService:
    """
    Base CreateReadUpdateDelete Class
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def truncate(**kwargs):
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
    def create(table: str, *, columns: list = '', values: list):
        """
        Формирует запрос INSERT
        :param table: Название таблицы
        :type table: str
        :param columns: Название столбцов таблицы, можно не указывать -
            тогда будет вставка по всей таблице
        :type columns: list
        :param values: Значения которые нужно вставить в таблицу,
            по стандарту значения должы
        :type values:
        :return:
        :rtype:
        """
        if type(values) == list and type(columns) == list and \
                len(columns) != len(values):
            raise WrongQueryError

        if type(columns) == list:
            columns_ = f"({', '.join(columns)})"
        else:
            columns_ = ''

        if type(values) == list:
            values_ = f"""VALUES ('{"', '".join(
                list(map(lambda x: str(x), values)))}')"""
        else:
            values_ = values

        query = """INSERT INTO %s%s VALUES('%s');""" % (table,
                                                        columns_,
                                                        values_)
        return query

    @staticmethod
    def read(table: str, *, columns: list | str, **kwargs):
        where = []
        if type(columns) == str:
            columns = [columns]
        if kwargs:
            for key, value in kwargs.items():
                if not where:
                    where.append(f"WHERE {key} = ('{value}')")
                else:
                    where.append(f"AND {key} = ('{value}')")
        return ("""SELECT %s FROM %s %s;""" % (', '.join(columns),
                                               table,
                                               ' '.join(where)))

    @staticmethod
    def unite(table: str, *, column: str, values: list, **kwargs: str):
        where = []
        if kwargs:
            for key, value in kwargs.items():
                if not where:
                    where.append(f"WHERE {key} = ('{value}')")
                else:
                    where.append(f"AND {key} = ('{value}')")
        return ("""UPDATE %s SET %s = %s || '{{"%s"}}' %s;""" % (table,
                                                                 column,
                                                                 column,
                                                                 '", "'.join(values),
                                                                 ' '.join(where)))

    @staticmethod
    def update(table: str, *, columns: list[str], values: list[Any], array: bool = False, **kwargs: str):
        center = []
        where = []
        if kwargs:
            for key, value in kwargs.items():
                if not where:
                    where.append(f"WHERE {key} = ('{value}')")
                else:
                    where.append(f"AND {key} = ('{value}')")

        for column, value in zip(columns, values):
            update_query = "%s = ('%s'), " % (column, value)
            if array:
                update_query = "%s = (ARRAY%s::text[]), " % (column, value)
            center.append(update_query)

        text = 'UPDATE %s SET ' % table + '\n'.join(center)[:-2] + ' ' + ' '.join(where) + ';'
        return text

    @staticmethod
    def delete(table: str, **kwargs: str):
        where = []
        if kwargs:
            for key, value in kwargs.items():
                if not where:
                    where.append(f"WHERE {key} = ('{value}')")
                else:
                    where.append(f"AND {key} = ('{value}')")
        return """DELETE FROM %s %s;""" % (table, ' '.join(where))


class JsonbCRUDService(CRUDService):
    @staticmethod
    def update(table: str, *, column: str, value: Any, path: list, add_key: bool = True,
               array: bool = False, **kwargs: str):
        where = []
        if kwargs:
            for k, v in kwargs.items():
                if not where:
                    where.append(f"WHERE {k} = ('{v}')")
                else:
                    where.append(f"AND {k} = ('{v}')")
        value = f'"{value}"'
        if array:
            value = f'[{value}]'
        return ("""UPDATE %s SET %s = jsonb_set(%s, '{"%s"}', '%s', %s) %s;""" % (table,
                                                                                  column,
                                                                                  column,
                                                                                  '", "'.join(path),
                                                                                  value,
                                                                                  add_key,
                                                                                  ' '.join(where)))

    @staticmethod
    def unite(table: str, *, column: str, value: Any, path: list,
              array: bool = False, add_key: bool = True, **kwargs: str):
        where = []
        if kwargs:
            for k, v in kwargs.items():
                if not where:
                    where.append(f"WHERE {k} = ('{v}')")
                else:
                    where.append(f"AND {k} = ('{v}')")
        value = f'"{value}"'
        if array:
            value = f'[{value}]'
        return ("""UPDATE %s SET %s = jsonb_set(%s, '{%s}', %s->'%s' || '%s', %s) %s;""" % (table,
                                                                                            column,
                                                                                            column,
                                                                                            ", ".join(path),
                                                                                            column,
                                                                                            "'->'".join(path),
                                                                                            value,
                                                                                            add_key,
                                                                                            ''.join(where)))

    @staticmethod
    def read(table: str, *, columns: str, path: list, **kwargs):
        where = []
        if kwargs:
            for key, value in kwargs.items():
                if not where:
                    where.append(f"WHERE {key} = ('{value}')")
                else:
                    where.append(f"AND {key} = ('{value}')")

        src_path = ''
        if path:
            src_path = f"""->'{"'->'".join(path)}'"""
        return ("""SELECT %s%s FROM %s %s;""" % (columns,
                                                 src_path,
                                                 table,
                                                 ' '.join(where)))
