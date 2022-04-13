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


def update_player_match_stats(match_data, player_name, match):
    fixture_id = match["id"]
    date = match["date"]
    if date not in match_data:
        match_data[date] = {}
    if player_name not in match_data[date]:
        match_data[date][player_name] = {
            "npxG": cast_float_safe(match["npxG"]),
            "xA": cast_float_safe(match["xA"])
        }


# TODO: take in gameweek or set of dates as argument to filter matches
async def get_player_understat_data():
    players = get_player_list()
    match_data = {}
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        for player in players:
            player_ustat_id = player["understat_id"]
            player_name = player["fpl_name"]
            matches = await understat.get_player_matches(
                player_ustat_id, season=CURRENT_SEASON[:-3]
            )
            for match in matches:
                update_player_match_stats(match_data, player_name, match)
        return match_data


if __name__ == "__main__":
    db = MySQLManager()
    fixtures = db.get_fixtures()
    id_map = uid_to_fpl_name()
    match_data = asyncio.run(get_player_understat_data())
    today = date.today()
    for fixture in fixtures:
        fixture_id = fixture[0]
        date = fixture[2]
        if date is None or date > today:
            continue
        for player_name, stats in match_data[date.strftime("%Y-%m-%d")].items():
            db.update_row(
                "player_gws",
                {"fixture_id": fixture_id, "player_name": player_name},
                {"npxG": stats["npxG"], "xA": stats["xA"]}
            )
