import mysql.connector
from mysql.connector.locales.eng import client_error
from mysql.connector.errors import IntegrityError
from typing import Any, List, Optional


def prepare_string(val: Any) -> str:
    if val is None:
        return "NULL"
    elif isinstance(val, str):
        return "'{}'".format(val.replace("'", "''"))
    else:
        return str(val)


class MySQLManager:

    def __init__(self):
        self.cnx = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database="fplcoachdb",
        )

    def writerows(self, rows: List[dict], table_name: str) -> None:
        cursor = self.cnx.cursor()
        col_names = rows[0].keys()
        cols = ",".join(col_names)
        for row in rows:
            inserts = ",".join([prepare_string(row[c]) for c in col_names])
            updates = ",".join([c + " = " + prepare_string(row[c]) for c in col_names])
            cmd = "INSERT INTO {} ({}) VALUES ({}) ON DUPLICATE KEY UPDATE {}".format(
                table_name, cols, inserts, updates)
            cursor.execute(cmd)
        self.cnx.commit()

    def exec_query(self, query):
        cursor = self.cnx.cursor()
        cursor.execute(query)
        self.cnx.commit()

    def get_fixtures(self, gameweeks = None):
        cursor = self.cnx.cursor()
        query = "SELECT * FROM fixtures"
        if isinstance(gameweeks, tuple):
            lower = gameweeks[0] if gameweeks[0] is not None else 1
            upper = gameweeks[1] if gameweeks[1] is not None else 38
            query += " WHERE gameweek >= {} AND gameweek <= {}".format(lower, upper)
        elif isinstance(gameweeks, int):
            query += " WHERE gameweek = {}".format(gameweeks)
        query += " ORDER BY gameweek"
        cursor.execute(query)
        return cursor.fetchall()
