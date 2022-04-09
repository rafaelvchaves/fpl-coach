import aiohttp
import asyncio
import os
import requests
from constants import CURRENT_SEASON, FPL_PLAYER_URL, UNDERSTAT_PLAYER_FILE
import datetime
from db import MySQLManager
from players import get_player_list
from teams import id_to_name_map
from typing import Dict, List, Optional, Tuple, Union
from understat import Understat
from utils import *

# TODO: use get_league_results to get all of the understat fixture ids,
# and then use get_match_players only for the desired matches.


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
    if os.path.exists(UNDERSTAT_PLAYER_FILE):
        ujson = from_json(UNDERSTAT_PLAYER_FILE)
        player_map = ujson["matches"]
        last_updated = ujson["last_updated"]
    else:
        player_map = {}
        last_updated = None
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        print("Fetching player Understat data...")
        for player in players:
            name = player["name"]
            matches = await understat.get_player_matches(
                player["understat_id"], season=CURRENT_SEASON[:-3]
            )
            for match in reversed(matches):
                date = match["date"]
                if last_updated is not None and last_updated > date:
                    break
                if date not in player_map:
                    player_map[date] = {}
                if name not in player_map[date]:
                    player_map[date][name] = {
                        "npxG": float(match["npxG"]),
                        "xA": float(match["xA"])
                    }
        print("Done")
        today = datetime.date.today().strftime("%Y-%m-%d")
        j = {"matches": player_map, "last_updated": today}
        to_json(UNDERSTAT_PLAYER_FILE, j)
        return player_map

# understat_player_data = asyncio.run(get_player_understat_data())
# asyncio.run(get_league_data())


def get_player_xg(name: str, date: str) -> Tuple[Optional[float], Optional[float]]:
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


def get_player_gw_json(player: dict, match: dict, price: float):
    name = player["name"]
    date = parse_date(match["kickoff_time"])
    # npxG, xA = get_player_xg(name, date)
    return {
        "player_name": name,
        "fixture_id": match.get("fixture", match.get("id", None)),
        "team": player["team_name"],
        "minutes_played": match.get("minutes", None),
        "npxG": None,
        "xA": None,
        "bonus": match.get("bonus", None),
        "total_points": match.get("total_points", None),
        "price": price
    }


def add_fixtures(rows: List[dict], player: dict, fpl_player_data: Dict[str, List[dict]], old: bool) -> None:
    old_fixtures = fpl_player_data["history"]
    upcoming_fixtures = fpl_player_data["fixtures"]
    # probably will fail in GW1 next season
    current_price = old_fixtures[-1]["value"] / 10
    if old:
        for match in old_fixtures:
            row = get_player_gw_json(
                player, match, match["value"] / 10)
            rows.append(row)
    for match in upcoming_fixtures:
        row = get_player_gw_json(
            player, match, current_price)
        rows.append(row)


def fetch_gw_data(gameweeks: Union[int, Tuple[int]], old : bool) -> List[dict]:
    tid_map = id_to_name_map()
    players = get_player_list()
    rows = []
    print("Fetching gameweek data...")
    for player in players:
        player_url = FPL_PLAYER_URL.format(player["fpl_id"])
        fpl_player_data = requests.get(player_url).json()
        add_fixtures(rows, player, fpl_player_data, old=old)
    print("Done")
    return rows



if __name__ == "__main__":
    db = MySQLManager()
    rows = fetch_gw_data(None, old=True)
    db.writerows(rows, "player_gws")
