import argparse
from db import *
from utils import get_current_gw
from prettytable import PrettyTable

parser = argparse.ArgumentParser(description="Get FPL point projections")
parser.add_argument("--start_gw", dest="start_gw", default=get_current_gw() + 1,
                    help="the starting gameweek to retrieve data from")
parser.add_argument("--num_gws", dest="num_gws", default=1,
                    help="the number of gameweeks ahead to retrieve data from, including the starting gw.")
parser.add_argument("--pos", dest="position", default=None,
                    help="position to filter by (G, D, M, F).")
parser.add_argument("--player", dest="player", default=None,
                    help="player's name to filter by.")
parser.add_argument("--limit", dest="limit", default=None,
                    help="maximum number of results to display.")


def optional(name, val):
    return "{} = {}".format(name, prepare_string(val)) if val is not None else "TRUE"


args = parser.parse_args()
start_gw = int(args.start_gw)
num_gws = int(args.num_gws)
player = args.player
position = args.position
limit = args.limit
db = MySQLManager()
my_table = PrettyTable()
my_table.field_names = ["Name", "GWs", "Team", "Opponents", "xP"]
with open("../scripts/predict.sql") as f:
    query = f.read()
    clauses = [
        "gameweek >= {}".format(start_gw),
        "gameweek <= {}".format(start_gw + num_gws - 1),
        optional("player_name", player),
        optional("position", position)
    ]
    where_clause = " AND ".join(clauses)
    if limit is not None:
      query += " LIMIT {}".format(limit)
    query = query.format(where_clause)
    for player in db.exec_query(query):
        my_table.add_row(player)
    print(my_table)
