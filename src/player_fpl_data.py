import requests
from constants import FPL_PLAYER_URL
from db import MySQLManager
from players import get_player_list
from typing import Dict, List, Optional, Tuple, Union
from utils import *

translate_stat = {
    "goal": "goals_scored",
    "assist": "assists",
    "bonus": "bonus",
    "cs": "clean_sheets",
    "concede": "goals_conceded"
}
params = from_json("../data/params.json")


def get_stat_points(stat, position, match):
    if stat == "minutes":
        minutes = match[stat]
        return int(minutes > 0) + int(minutes > 59)
    value = params[position][stat + "_value"]
    fpl_stat_name = translate_stat[stat]
    if fpl_stat_name not in match:
        return None
    count = match[fpl_stat_name]
    return count * value if stat != "concede" else count // 2 * value


def get_player_gw_extra(player: dict, match: dict) -> dict:
    stats = ["goal", "assist", "bonus", "cs", "concede", "minutes"]
    return {
        "player_name": player["fpl_name"],
        "fixture_id": match.get("fixture", match.get("id", None)),
        **{stat + "_points": get_stat_points(stat, player["position"], match) for stat in stats},
        **{stat + "_xP": None for stat in stats},
        "xP": None,
        "total_points": match.get("total_points", None)
    }


def get_player_gw_json(player: dict, match: dict, price: float) -> dict:
    return {
        "player_name": player["fpl_name"],
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


def add_fixtures(rows: List[dict], extra_rows: List[dict], player: dict, fpl_player_data: Dict[str, List[dict]], old: bool) -> None:
    old_fixtures = fpl_player_data["history"]
    upcoming_fixtures = fpl_player_data["fixtures"]
    if old:
        for match in old_fixtures:
            rows.append(get_player_gw_json(player, match, match["value"] / 10))
            extra_rows.append(get_player_gw_extra(player, match))
    for match in upcoming_fixtures:
        rows.append(get_player_gw_json(player, match, None))


def fetch_gw_data(gameweeks: Union[int, Tuple[int]], old: bool) -> List[dict]:
    players = get_player_list()
    rows = []
    extra_rows = []
    for player in players:
        player_url = FPL_PLAYER_URL.format(player["fpl_id"])
        fpl_player_data = requests.get(player_url).json()
        add_fixtures(rows, extra_rows, player, fpl_player_data, old=old)
    return rows, extra_rows


if __name__ == "__main__":
    db = MySQLManager()
    rows, extra_rows = fetch_gw_data(None, old=True)
    db.insert_rows("player_gws", rows)
    db.insert_rows("player_gws_extra", extra_rows)
