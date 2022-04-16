import argparse
from db import *
from utils import get_current_gw
from prettytable import PrettyTable

current_gw = get_current_gw()


def parse_args():
    parser = argparse.ArgumentParser(description="Get FPL point projections")
    parser.add_argument("--gws", dest="gws", default=current_gw + 1,
                        help="gw(s) to get data from, can either be a single integer or a range such as 1-38.")
    parser.add_argument("--position", dest="position", default=None,
                        help="position to filter by (G, D, M, F).")
    parser.add_argument("--player", dest="player", default=None,
                        help="player's name to filter by.")
    parser.add_argument("--limit", dest="limit", default=None,
                        help="maximum number of results to display.")
    parser.add_argument("--show_opponents", dest="show_opp", action="store_true",
                        default=False, help="whether to show opponents or not.")
    parser.add_argument("--price_limit", dest="price_lim",
                        default=None, help="price limit")
    parser.add_argument("--sort_by", dest="sort_key", default="xP", help="a column to sort by.")
    return parser.parse_args()


def optional(name, val, cmp="="):
    return "{} {} {}".format(name, cmp, prepare_string(val)) if val is not None else "TRUE"


def query_database(args):
    db = MySQLManager()
    try:
        start_gw, end_gw = [int(gw) for gw in args.gws.split("-")]
    except:
        start_gw = end_gw = int(args.gws)
    f = open("../scripts/predict.sql")
    query = f.read()

    selected_cols = []
    group_cols = ["player_name", "position"]
    if args.show_opp:
        selected_cols.append("GROUP_CONCAT(opponent SEPARATOR ', ') AS opponents")
    selected_cols.append("SUM(xP) AS xP")
    if end_gw <= current_gw:
        selected_cols.append("SUM(total_points) AS points")
        selected_cols.append("ROUND(SUM(xP) - SUM(total_points)) AS delta")
    select_clause = ",".join(selected_cols)
    group_by_clause = ",".join(group_cols)

    filters = [
        "gameweek >= {}".format(start_gw),
        "gameweek <= {}".format(end_gw),
        optional("player_name", args.player),
        optional("position", args.position),
        optional("price", args.price_lim, "<=")
    ]
    where_clause = " AND ".join(filters)

    query += " ORDER BY {} DESC".format(args.sort_key)
    if args.limit is not None:
        query += " LIMIT {}".format(args.limit)
    query = query.format(select_clause, where_clause, group_by_clause)
    print(query)
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
