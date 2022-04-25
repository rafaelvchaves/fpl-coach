import argparse
from constants import OPTIONS_FILE, PREDICT_SCRIPT
from db import *
from utils import from_json, get_current_gw
from prettytable import PrettyTable

current_gw = get_current_gw()


def parse_args():
    parser = argparse.ArgumentParser(description="Get FPL point projections")
    options = from_json(OPTIONS_FILE)
    options["--gws"]["default"] = current_gw + 1
    for option, info in options.items():
        parser.add_argument(option, **info)
    return parser.parse_args()


def optional(name, val, cmp="="):
    return f"{name} {cmp} {prepare_string(val)}" if val is not None else "TRUE"


def query_database(args):
    db = MySQLManager()
    try:
        start_gw, end_gw = [int(gw) for gw in args.gws.split("-")]
    except:
        start_gw = end_gw = int(args.gws)
    f = open(PREDICT_SCRIPT)
    query = f.read()
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
