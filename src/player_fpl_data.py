import requests
from constants import FPL_GAMEWEEK_URL, FPL_PLAYER_URL
from db import MySQLManager
from players import get_player_list, create_player_map
from typing import Dict, List, Optional, Tuple, Union
from utils import *

# translate_stat = {
#     "goal": "goals_scored",
#     "assist": "assists",
#     "bonus": "bonus",
#     "cs": "clean_sheets",
#     "concede": "goals_conceded"
# }
# params = from_json("../data/params.json")


# def get_stat_points(stat, position, match):
#     if stat == "minutes":
#         minutes = match[stat]
#         return int(minutes > 0) + int(minutes > 59)
#     value = params[position][stat + "_value"]
#     fpl_stat_name = translate_stat[stat]
#     if fpl_stat_name not in match:
#         return None
#     count = match[fpl_stat_name]
#     return count * value if stat != "concede" else count // 2 * value


# def get_player_gw_extra(player: dict, match: dict) -> dict:
#     stats = ["goal", "assist", "bonus", "cs", "concede", "minutes"]
#     return {
#         "player_name": player["fpl_name"],
#         "fixture_id": match.get("fixture", match.get("id", None)),
#         **{stat + "_points": get_stat_points(stat, player["position"], match) for stat in stats},
#         **{stat + "_xP": None for stat in stats},
#         "xP": None,
#         "total_points": match.get("total_points", None)
#     }


# def get_player_gw_json(player: dict, match: dict, price: float, finished: bool) -> dict:
#     return {
#         "player_name": player["fpl_name"],
#         "fixture_id": match.get("fixture", match.get("id", None)),
#         "team": player["team_name"],
#         "minutes": match["minutes"] if finished else None,
#         "npxG": None,  # filled in by understat
#         "xA": None,  # filled in by understat
#         "bonus": match.get("bonus", None),
#         "total_points": match.get("total_points", None),
#         "price": price,
#         "xP": None  # filled in by prediction model
#     }


# def add_fixtures(rows: List[dict], extra_rows: List[dict], player: dict, fpl_player_data: Dict[str, List[dict]], old: bool) -> None:
#     old_fixtures = fpl_player_data["history"]
#     upcoming_fixtures = fpl_player_data["fixtures"]
#     if old:
#         for match in old_fixtures:
#             rows.append(get_player_gw_json(
#                 player, match, match["value"] / 10, True))
#             extra_rows.append(get_player_gw_extra(player, match))
#     for match in upcoming_fixtures:
#         rows.append(get_player_gw_json(player, match, None, match["finished"]))
#         extra_rows.append(get_player_gw_extra(player, match))


# def fetch_gw_data(gameweeks: Union[int, Tuple[int]], old: bool) -> List[dict]:
#     players = get_player_list()
#     rows = []
#     extra_rows = []
#     for player in players:
#         player_url = FPL_PLAYER_URL.format(player["fpl_id"])
#         fpl_player_data = requests.get(player_url).json()
#         add_fixtures(rows, extra_rows, player, fpl_player_data, old=old)
#     return rows, extra_rows


desired_stats = {"minutes", "goals_scored", "assists",
                 "clean_sheets", "goals_conceded", "bonus", "saves"}


def get_player_data(player_json: dict, stats: List[dict]) -> None:
    total_points = 0
    for stat in stats:
        stat_name = stat["identifier"]
        total_points += stat["points"]
        if stat_name in desired_stats:
            player_json[stat_name] = stat["value"]
    player_json["total_points"] = total_points
    return player_json


def fetch_gw_data(gws: Optional[Union[int, Tuple[int]]]) -> List[dict]:
    get_name = create_player_map("fpl_id", "fpl_name")
    get_team = create_player_map("fpl_id", "team_name")
    rows = []
    extra_rows = []
    if gws is None:
        start, end = 1, get_current_gw()
    elif isinstance(gws, int):
        start = end = gws
    elif isinstance(gws, tuple):
        start, end = gws
    for gw in range(start, end + 1):
        gw_url = FPL_GAMEWEEK_URL.format(gw)
        gw_data = requests.get(gw_url).json()["elements"]
        for player in gw_data:
            player_id = player["id"]
            matches = player["explain"]
            try:
                name = get_name[player_id]
                team = get_team[player_id]
            except:
                continue # temporary fix because some FPL players that left aren't in the database
            for match in matches:
                base_player_json = {
                    "player_name": name,
                    "fixture_id": match["fixture"],
                }
                extra_rows.append(base_player_json)
                player_json = {
                    **base_player_json,
                    "team": team,
                    **{stat: 0 for stat in desired_stats},
                    "total_points": 0
                }
                if player["stats"]["minutes"] == 0:
                    rows.append(player_json)
                else:
                    rows.append(get_player_data(player_json, match["stats"]))
    return rows, extra_rows


if __name__ == "__main__":
    db = MySQLManager()
    rows, extra_rows = fetch_gw_data(None)
    db.insert_rows("player_gws", rows)
    db.insert_rows("player_gws_predicted", extra_rows)
