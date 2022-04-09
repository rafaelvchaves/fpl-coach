import mysql.connector
from mysql.connector.locales.eng import client_error
from mysql.connector.errors import IntegrityError
from typing import Any, List, Optional


def extract_value(val: Any) -> str:
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
        keys = rows[0].keys()
        cols = ",".join(keys)
        for row in rows:
            vals = ",".join([extract_value(row[k]) for k in keys])
            sql = "INSERT INTO {} ({}) VALUES ({})".format(
                table_name, cols, vals)
            try:
                cursor.execute(sql)
            except IntegrityError as e:
                if e.errno == 1062:
                    # Already in table, can just skip over for now
                    continue
                print(e)
                exit(1)
        self.cnx.commit()

    def read_table(self, table_name : str, sort_by : Optional[str]):
        cursor = self.cnx.cursor()
        query = "SELECT * FROM {}".format(table_name)
        if sort_by is not None:
            query += " ORDER BY {}".format(sort_by)
        cursor.execute(query)
        return cursor.fetchall()  

    def query(self, query):
        cursor = self.cnx.cursor()
        cursor.execute(query)
        return cursor.fetchall()      

    def get_fixtures(self, gameweeks):
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
