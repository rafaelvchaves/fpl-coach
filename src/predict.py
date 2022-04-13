import argparse
from db import *
from utils import get_current_gw
from prettytable import PrettyTable


def parse_args():
    parser = argparse.ArgumentParser(description="Get FPL point projections")
    parser.add_argument("--gws", dest="gws", default=get_current_gw() + 1,
                        help="gw(s) to get data from, can either be a single integer or a range such as 1-38.")
    parser.add_argument("--position", dest="position", default=None,
                        help="position to filter by (G, D, M, F).")
    parser.add_argument("--player", dest="player", default=None,
                        help="player's name to filter by.")
    parser.add_argument("--limit", dest="limit", default=None,
                        help="maximum number of results to display.")
    parser.add_argument("--show_opponents", dest='show_opp', action='store_true',
                        default=False, help="whether to show opponents or not")
    return parser.parse_args()


def optional(name, val):
    return "{} = {}".format(name, prepare_string(val)) if val is not None else "TRUE"


def query_database(args):
    db = MySQLManager()
    try:
        start_gw, end_gw = args.gws.split("-")
    except:
        start_gw = end_gw = int(args.gws)
    f = open("../scripts/predict.sql")
    query = f.read()
    clauses = [
        "gameweek >= {}".format(start_gw),
        "gameweek <= {}".format(end_gw),
        optional("player_name", args.player),
        optional("position", args.position)
    ]
    select_clause = "GROUP_CONCAT(opponent SEPARATOR ', ') AS opponents," if args.show_opp else ""
    where_clause = " AND ".join(clauses)
    if args.limit is not None:
        query += " LIMIT {}".format(args.limit)
    query = query.format(select_clause, where_clause)
    cols, players = db.exec_query(query, get_col_names=True)
    f.close()
    return cols, players


def main():
    args = parse_args()
    cols, players = query_database(args)
    player_table = PrettyTable()
    player_table.field_names = cols
    for player in players:
        player_table.add_row(player)
    print(player_table)

if __name__ == "__main__":
    main()
