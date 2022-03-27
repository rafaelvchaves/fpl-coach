import mysql.connector
class DB:
    # def __del__(self):
    #     self.db.close()

    def __init__(self):
        self.db = mysql.connector.connect(
            host="host",
            user="root",
            password="password",
            database="fplcoach",
        )
        print("Started database connection")

    def writerows(self):
        cursor = self.db.cursor()