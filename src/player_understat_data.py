import aiohttp
import asyncio
from constants import CURRENT_SEASON
from db import MySQLManager
from fixtures import fixture_id_map
from players import get_player_list
from understat import Understat
from utils import *
from typing import Any, Dict

fixture_id_map = fixture_id_map()
MatchData = Dict[int, Dict[str, Dict[str, Any]]]


def update_player_match_stats(match_data: MatchData, player_name: str, match: dict) -> None:
    """Updates match_data with given player's stats.

    Args:
        match_data: A dictionary mapping an FPL fixture id to a dictionary,
          which maps a player name from that match to a dictionary with their
          stats from that match. For example, if Bukayo Saka recorded 0.277
          npxG and 0.323 xA in fixture 19, then match_data looks like:
          {
              ...,
              19: {
                  "Bukayo Saka": {"npxG": 0.277, "xA": 0.323},
                  ...
              },
              ...
          }
        player_name: The name of the player to update
        match: A dictionary of match data/metadata, for example the understat
          id of the match or the number of goals that the player scored in that
          match.

    Returns:
        None. Adds a new mapping to match_data. 
    """
    ustat_id = int(match["id"])
    if ustat_id not in fixture_id_map:
        # not a premier league game
        return
    fixture_id = fixture_id_map[ustat_id]
    if fixture_id not in match_data:
        match_data[fixture_id] = {}
    if player_name not in match_data[fixture_id]:
        match_data[fixture_id][player_name] = {
            "npxG": cast_float_safe(match["npxG"]),
            "xA": cast_float_safe(match["xA"])
        }


# TODO: take in gameweek or set of dates as argument to filter matches
async def get_player_understat_data() -> MatchData:
    """Fetch all player's match data from the current season."""
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
    match_data = asyncio.run(get_player_understat_data())
    for fixture in fixtures:
        fixture_id = fixture[0]
        if not fixture_id in match_data:
            # Understat does not have data for this fixture yet
            continue
        for player_name, stats in match_data[fixture_id].items():
            db.update_row(
                "player_gws",
                {"fixture_id": fixture_id, "player_name": player_name},
                {**stats}
            )
