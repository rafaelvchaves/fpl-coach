import aiohttp
import asyncio
import csv
import json
import requests
from constants import CURRENT_SEASON, FPL_BASE_URL, FPL_PLAYER_URL, GW_HISTORY_FILE
from datetime import datetime
from players import get_player_list
from teams import id_to_name_map
from understat import Understat
from utils import compare_by_index


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
        with open("test.json", "w") as f:
            json.dump(player_map, f)
        print("Done")
        return player_map


def get_player_xg(name, date, understat_player_data):
    """Finds player's npxG and xA from game on given date.
    
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


def convert_date(date):
    if date is None:
        return None
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")


def get_player_match_info(player, match, understat_player_data):
    name = player["name"]
    position = player["position"]
    gw = match.get("round", match.get("event", None))
    fixture_id = match.get("fixture", match.get("id", None))
    date = convert_date(match["kickoff_time"])
    home = match.get("was_home", match.get("is_home", None))
    minutes = match.get("minutes", None)
    bonus = match.get("bonus", None)
    points = match.get("total_points", None)
    npxG, xA = get_player_xg(name, date, understat_player_data)
    return [gw, fixture_id, date, name,
            position, home, minutes, bonus, points, npxG, xA]

def add_fixtures(rows, player, understat_player_data, fixtures):
  for match in fixtures:
    row = get_player_match_info(player, match, understat_player_data)
    rows.append(row)

def fetch_gw_data(all=True):
    f = open(GW_HISTORY_FILE, "w")
    writer = csv.writer(f)
    header = ["gw", "fixture_id", "date", "name",
              "position", "home", "minutes", "bonus", "points", "npxG", "xA"]
    writer.writerow(header)
    tid_map = id_to_name_map()
    players = get_player_list()
    rows = []
    understat_player_data = asyncio.run(get_player_understat_data())
    print("Fetching gameweek data...")
    for player in players:
        fpl_id = player["fpl_id"]
        player_info = requests.get(FPL_PLAYER_URL.format(fpl_id)).json()
        old_fixtures = player_info["history"]
        next_fixtures = player_info["fixtures"]
        add_fixtures(rows, player, understat_player_data, old_fixtures)
        add_fixtures(rows, player, understat_player_data, next_fixtures)
        # for match in history:
        #     if match["team_h_score"] is None:
        #         continue
        #     row = get_player_match_info(player, match, understat_player_data)
        #     rows.append(row)
        # fixtures = player_info["fixtures"]
        # for match in fixtures:
        #     row = get_player_match_info(player, match, understat_player_data)
        #     rows.append(row)
    rows.sort(key=compare_by_index(2))
    writer.writerows(rows)
    print("Done")
    f.close()


if __name__ == "__main__":
    fetch_gw_data()
