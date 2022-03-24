import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="fplcoach_db"
)

cursor = db.cursor()

print(cursor.execute("""SELECT COUNT(*) FROM teams"""))