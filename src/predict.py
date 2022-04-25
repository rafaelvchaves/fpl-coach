"""A module for displaying point predictions."""
import argparse
from prettytable import PrettyTable
from constants import OPTIONS_FILE, PREDICT_SCRIPT
from db import MySQLManager
from utils import from_json, get_current_gw

current_gw = get_current_gw()


def parse_args():
    """Parses command line arguments, specified in the options file."""
    parser = argparse.ArgumentParser(description="Get FPL point projections")
    options = from_json(OPTIONS_FILE)
    options["--gws"]["default"] = current_gw + 1
    for option, info in options.items():
        parser.add_argument(option, **info)
    return parser.parse_args()


def optional(name, val, cmp="="):
    """Helper function for producing SQL clauses."""
    return f"{name} {cmp} {prepare_string(val)}" if val is not None else "TRUE"


def query_database(args):
    """Constructs a query based on cli arguments and returns results."""
    db = MySQLManager()
    try:
        start_gw, end_gw = [int(gw) for gw in args.gws.split("-")]
    except (ValueError, AttributeError):
        start_gw = end_gw = int(args.gws)
    with open(PREDICT_SCRIPT, encoding="utf-8") as sql_script:
        query = sql_script.read()
    selected_cols = []
    group_cols = ["player_name", "position"]
    if args.show_opp:
        selected_cols.append(
            "GROUP_CONCAT(opponent SEPARATOR ', ') AS opponents")
    selected_cols.append("SUM(xP) AS xP")
    if end_gw <= current_gw:
        selected_cols.append("SUM(total_points) AS points")
        selected_cols.append("ROUND(SUM(xP) - SUM(total_points)) AS delta")
    select_clause = ",".join(selected_cols)
    group_by_clause = ",".join(group_cols)
    filters = [
        f"gameweek >= {start_gw}",
        f"gameweek <= {end_gw}",
        optional("player_name", args.player),
        optional("position", args.position)
    ]
    where_clause = " AND ".join(filters)
    query += f" ORDER BY {args.sort_key} DESC"
    query += f" LIMIT {args.limit}"
    query = query.format(select_clause, where_clause, group_by_clause)
    cols, players = db.exec_query(query, get_col_names=True)
    return cols, players


if __name__ == "__main__":
    args = parse_args()
    cols, players = query_database(args)
    player_table = PrettyTable()
    player_table.field_names = cols
    for player in players:
        player_table.add_row(player)
    print(player_table)
