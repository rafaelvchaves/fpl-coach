import mysql.connector
from db import DB

d = DB()

# db = mysql.connector.connect(
#     host="host",
#     user="root",
#     password="password",
#     database="fplcoachdb",
# )

d.writerows({"id": 1, "name": "Rafael"}, "table")