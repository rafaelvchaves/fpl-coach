import aiohttp
import asyncio
import csv
import json
import requests
from constants import CURRENT_SEASON, FPL_BASE_URL, FPL_PLAYER_URL, GW_HISTORY_FILE
from datetime import datetime
from db import MySQLManager
from players import get_player_list
from teams import id_to_name_map
from typing import Dict, List, Optional, Tuple
from understat import Understat
from utils import compare_by_index


class PlayerGWDataCollector:
    def __init__(self):
        pass


async def get_player_understat_data():
    """Retrieves Understat player data from current season.

    Returns:
        A dictionary with dates as keys, mapping to another json object
        containing as keys all of the players playing on that date. Each of
        those keys maps to a json object containing the player's npxG and xA
        for that game. For example,
            {
                "2021-08-13": {
                    "Bukayo Saka" : {
                        "npxG": ...,
                        "xA": ...
                    },
                    ...
                },
                ...
            }
    """
    players = get_player_list()
    player_map = {}
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        print("Fetching player Understat data...")
        for player in players:
            name = player["name"]
            matches = await understat.get_player_matches(
                player["understat_id"], season=CURRENT_SEASON[:-3]
            )
            for match in matches:
                date = match["date"]
                if date not in player_map:
                    player_map[date] = {}
                if name not in player_map[date]:
                    player_map[date][name] = {
                        "npxG": float(match["npxG"]),
                        "xA": float(match["xA"])
                    }
        print("Done")
        return player_map


def get_player_xg(name: str, date: str, understat_player_data) -> Tuple[Optional[float], Optional[float]]:
    """Finds player's npxG and xA from game on given date.

    Args:
        name: The name of the player
        date: The date of the match to get data from, in the form YYYY-MM-DD.

    Returns:
        A tuple (npxG, xA) if such statistics exist for the player on that date.
        (None, None) otherwise.
    """
    if date not in understat_player_data:
        return None, None
    game_data = understat_player_data[date]
    if name not in game_data:
        # Game has happened but understat has not updated stats yet
        return None, None
    player_data = understat_player_data[date][name]
    npxG = round(player_data["npxG"], 3)
    xA = round(player_data["xA"], 3)
    return npxG, xA


def convert_date(date: Optional[str]) -> str:
    if date is None:
        return None
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")


def get_player_gw_json(player : dict, match : dict, price : float, understat_player_data):
    name = player["name"]
    date = convert_date(match["kickoff_time"])
    npxG, xA = get_player_xg(name, date, understat_player_data)
    return {
        "player_id": player["fpl_id"],
        "fixture_id": match.get("fixture", match.get("id", None)),
        "team": player["team_name"],
        "minutes_played": match.get("minutes", None),
        "npxG": npxG,
        "xA": xA,
        "bonus": match.get("bonus", None),
        "total_points": match.get("total_points", None),
        "price": price
    }
#   gameweek INT,
#   fixture_id INT NOT NULL,
#   team VARCHAR(255) NOT NULL,
#   opponent VARCHAR(255) NOT NULL,
#   home BOOLEAN NOT NULL,
#   xG FLOAT,
#   xGA FLOAT,


#   id INT AUTO_INCREMENT PRIMARY KEY,
#   team_name VARCHAR(255),
#   gameweek INT NOT NULL,
#   xG FLOAT,
#   xGA FLOAT,
#   FOREIGN KEY (team_name) REFERENCES teams(fpl_name)

#   player_id INT,
#   gameweek INT,
#   fixture_id INT,
#   team_id INT,
#   opponent_id INT,
#   minutes_played INT,
#   npxg FLOAT,
#   xa FLOAT,
#   bonus_points INT,
#   total_points INT,
#   price FLOAT,

def add_fixtures(rows: List[dict], player: dict, understat_player_data: Dict[str, dict], fpl_player_data: Dict[str, List[dict]]) -> None:
    old_fixtures = fpl_player_data["history"]
    upcoming_fixtures = fpl_player_data["fixtures"]
    # probably will fail in GW1 next season
    current_price = old_fixtures[-1]["value"] / 10
    for match in old_fixtures:
        row = get_player_gw_json(
            player, match, match["value"] / 10, understat_player_data)
        rows.append(row)
    for match in upcoming_fixtures:
        row = get_player_gw_json(
            player, match, current_price, understat_player_data)
        rows.append(row)


def fetch_gw_data() -> List[dict]:
    tid_map = id_to_name_map()
    players = get_player_list()
    rows = []
    understat_player_data = asyncio.run(get_player_understat_data())
    print("Fetching gameweek data...")
    for player in players:
        player_url = FPL_PLAYER_URL.format(player["fpl_id"])
        fpl_player_data = requests.get(player_url).json()
        add_fixtures(rows, player, understat_player_data, fpl_player_data)
    print("Done")
    return rows


if __name__ == "__main__":
    db = MySQLManager()
    gw_data = fetch_gw_data()
    db.writerows(gw_data, "player_gws")
