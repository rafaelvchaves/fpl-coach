import mysql.connector
from mysql.connector.locales.eng import client_error
from mysql.connector.errors import IntegrityError
from typing import Any, List

def extract_value(val : Any) -> str:
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
        print("Started database connection")

    def writerows(self, rows : List[dict], table_name : str) -> None:
        cursor = self.cnx.cursor()
        keys = rows[0].keys()
        cols = ",".join(keys)
        for row in rows:
            vals = ",".join([extract_value(row[k]) for k in keys])
            sql = "INSERT INTO {} ({}) VALUES ({})".format(table_name, cols, vals)
            try:
                cursor.execute(sql)
            except IntegrityError as e:
                if e.errno == 1062:
                    # Already in table, can just skip over for now
                    continue
                print(e)
                exit(1)
        self.cnx.commit()
