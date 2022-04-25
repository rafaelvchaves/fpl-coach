"""A module for displaying point predictions for a specific manager's team."""
import argparse
from prettytable import PrettyTable
from constants import MY_TEAM_SCRIPT, TEAM_OPTIONS_FILE
from db import MySQLManager
from utils import from_json, get_current_gw

current_gw = get_current_gw()

# Horrific code duplication

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Get FPL point projections")
    options = from_json(TEAM_OPTIONS_FILE)
    options["--gws"]["default"] = current_gw + 1
    for option, info in options.items():
        parser.add_argument(option, **info)
    return parser.parse_args()


def query_database(args):
    """Constructs a query based on cli arguments and returns results."""
    db = MySQLManager()
    try:
        start_gw, end_gw = [int(gw) for gw in args.gws.split("-")]
    except (ValueError, AttributeError):
        start_gw = end_gw = int(args.gws)
    with open(MY_TEAM_SCRIPT, encoding="utf-8") as sql_script:
        query = sql_script.read()
    query = query.format(start_gw, end_gw)
    cols, players = db.exec_query(query, get_col_names=True)
    return cols, players


def main():
    """Parses command line arguments and queries database."""
    args = parse_args()
    cols, players = query_database(args)
    player_table = PrettyTable()
    player_table.field_names = cols
    for player in players:
        player_table.add_row(player)
    print(player_table)


if __name__ == "__main__":
    main()
