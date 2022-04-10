import aiohttp
import asyncio
from datetime import date
import os
from constants import CURRENT_SEASON, UNDERSTAT_PLAYER_FILE
from players import get_player_list, uid_to_fpl_name
from teams import id_to_name_map, understat_to_fpl_map
from understat import Understat
from utils import *
from db import MySQLManager


# async def get_player_understat_data(fixtures):
#     players = get_player_list()
#     if os.path.exists(UNDERSTAT_PLAYER_FILE):
#         ujson = from_json(UNDERSTAT_PLAYER_FILE)
#         player_map = ujson["matches"]
#         last_updated = ujson["last_updated"]
#     else:
#         player_map = {}
#         last_updated = None
#     async with aiohttp.ClientSession() as session:
#         understat = Understat(session)
#         print("Fetching player Understat data...")
#         for player in players:
#             name = player["name"]
#             matches = await understat.get_player_matches(
#                 player["understat_id"], season=CURRENT_SEASON[:-3]
#             )
#             for match in reversed(matches):
#                 fixture_id = match["id"]
#                 if last_updated is not None and last_updated > match["date"]:
#                     break
#                 if fixture_id not in player_map:
#                     player_map[fixture_id] = {}
#                 if name not in player_map[fixture_id]:
#                     player_map[fixture_id][name] = {
#                         "npxG": cast_float_safe(match["npxG"]),
#                         "xA": cast_float_safe(match["xA"])
#                     }
#         print("Done")
#         today = date.today().strftime("%Y-%m-%d")
#         j = {"matches": player_map, "last_updated": today}
#         to_json(UNDERSTAT_PLAYER_FILE, j)
#         return player_map


async def get_player_understat_data(fixtures):
    match_data = {}
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        for fixture in fixtures:
            fpl_id = fixture[0]
            understat_id = fixture[1]
            try:
                match_stats = await understat.get_match_players(understat_id)
            except Exception as e:
                continue
            if fpl_id not in match_data:
                match_data[fpl_id] = {}
            combined_match_stats = {**match_stats["h"], **match_stats["a"]}
            for player_match_id in combined_match_stats:
                player = combined_match_stats[player_match_id]
                player_id = int(player["player_id"])
                match_data[fpl_id][player_id] = {
                    "npxG": cast_float_safe(player["xG"]),
                    "xA": cast_float_safe(player["xA"])
                }
        return match_data


if __name__ == "__main__":
    db = MySQLManager()
    fixtures = db.get_fixtures()
    id_map = uid_to_fpl_name()
    match_data = asyncio.run(get_player_understat_data(fixtures))
    for fixture_id, players in match_data.items():
        for player_id, stats in players.items():
            fpl_name = id_map[int(player_id)]
            db.update_row(
                "player_gws",
                {"fixture_id": fixture_id, "player_name": fpl_name},
                {"npxG": stats["npxG"], "xA": stats["xA"]}
            )
