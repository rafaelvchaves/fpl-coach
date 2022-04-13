import requests
from constants import FPL_PLAYER_URL
from db import MySQLManager
from players import get_player_list
from typing import Dict, List, Optional, Tuple, Union
from utils import *


def get_player_gw_json(player: dict, match: dict, price: float):
    name = player["fpl_name"]
    date = parse_date(match["kickoff_time"])
    return {
        "player_name": name,
        "fixture_id": match.get("fixture", match.get("id", None)),
        "team": player["team_name"],
        "minutes": match.get("minutes", None),
        "npxG": None,  # filled in by understat
        "xA": None,  # filled in by understat
        "bonus": match.get("bonus", None),
        "total_points": match.get("total_points", None),
        "price": price,
        "xP": None  # filled in by prediction model
    }


def add_fixtures(rows: List[dict], player: dict, fpl_player_data: Dict[str, List[dict]], old: bool) -> None:
    old_fixtures = fpl_player_data["history"]
    upcoming_fixtures = fpl_player_data["fixtures"]
    if old:
        for match in old_fixtures:
            rows.append(get_player_gw_json(player, match, match["value"] / 10))
    for match in upcoming_fixtures:
        rows.append(get_player_gw_json(player, match, None))


def fetch_gw_data(gameweeks: Union[int, Tuple[int]], old: bool) -> List[dict]:
    players = get_player_list()
    rows = []
    for player in players:
        player_url = FPL_PLAYER_URL.format(player["fpl_id"])
        fpl_player_data = requests.get(player_url).json()
        add_fixtures(rows, player, fpl_player_data, old=old)
    return rows


if __name__ == "__main__":
    db = MySQLManager()
    rows = fetch_gw_data(None, old=True)
    db.insert_rows("player_gws", rows)
