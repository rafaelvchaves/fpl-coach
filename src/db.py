class DB:
    def __del__(self):
        self.db.close()

    def __init__(self):
        self.db = mysql.connector.connect(
            host="host",
            user="root",
            password="password",
            database="fplcoach",
        )
        print("Started database connection")

    def cursor(self):
        return self.db.cursor()