from typing import Any

from utils.exceptions import WrongQueryError


class CRUDService:
    """
    Base CreateReadUpdateDelete Class
    """

    @staticmethod
    def truncate(table: str):
        return "TRUNCATE TABLE %s" % table

    @staticmethod
    def create(table: str, *, columns: list, values: list):
        if len(columns) != len(values):
            raise WrongQueryError

        return ("""INSERT INTO %s(%s) VALUES('%s');""" % (table,
                                                          ", ".join(columns),
                                                          "', '".join(list(map(lambda x: str(x), values)))))

    @staticmethod
    def read(table: str, *, column: str, **kwargs):
        where = []
        if kwargs:
            for key, value in kwargs.items():
                if not where:
                    where.append(f"WHERE {key} = ('{value}')")
                else:
                    where.append(f"AND {key} = ('{value}')")
        return ("""SELECT %s FROM %s %s;""" % (column,
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
                update_query = "%s = (ARRAY[%s]::text[]), " % (column, value)
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
    def update(table: str, *, column: str, value: Any, path: list, add_key: bool = True, **kwargs: str):
        where = []
        if kwargs:
            for k, v in kwargs.items():
                if not where:
                    where.append(f"WHERE {k} = ('{v}')")
                else:
                    where.append(f"AND {k} = ('{v}')")
        return ("""UPDATE %s SET %s = jsonb_set(%s, '{"%s"}', '"%s"', %s) %s;""" % (table,
                                                                                    column,
                                                                                    column,
                                                                                    '", "'.join(path),
                                                                                    value,
                                                                                    add_key,
                                                                                    ' '.join(where)))

    @staticmethod
    def unite(table: str, *, column: str, value: Any, path: list, add_key: bool = True, **kwargs: str):
        where = []
        if kwargs:
            for key, value in kwargs.items():
                if not where:
                    where.append(f"WHERE {key} = ('{value}')")
                else:
                    where.append(f"AND {key} = ('{value}')")
        return ("""UPDATE %s SET %s = jsonb_set(%s, '{%s}', %s->'%s' || '"%s"', %s) %s;""" % (table,
                                                                                              column,
                                                                                              column,
                                                                                              ", ".join(path),
                                                                                              column,
                                                                                              "'->'".join(path),
                                                                                              value,
                                                                                              add_key,
                                                                                              ''.join(where)))

    @staticmethod
    def read(table: str, *, column: str, path: list, **kwargs):
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
        return ("""SELECT %s%s FROM %s %s;""" % (column,
                                                 src_path,
                                                 table,
                                                 ' '.join(where)))
