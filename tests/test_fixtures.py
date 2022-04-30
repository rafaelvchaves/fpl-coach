from fpl_coach.db import MySQLManager

db = MySQLManager()
df = db.get_df("""SELECT * FROM team_gws""")
assert len(df) == 760