import mysql.connector
from mysql.connector.locales.eng import client_error

def extract_value(val):
    if isinstance(val, str):
        return "'{}'".format(val)
    else:
        return str(val)

class DB:

    def __init__(self):
        self.cnx = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database="fplcoachdb",
        )
        print("Started database connection")

    def writerows(self, rows, table):
        cursor = self.cnx.cursor()
        keys = rows[0].keys()
        cols = ",".join(keys)
        for row in rows:
            vals = ",".join([extract_value(row[k]) for k in keys])
            sql = "INSERT INTO {} ({}) VALUES ({})".format(table, cols, vals)
            cursor.execute(sql)
        self.cnx.commit()
