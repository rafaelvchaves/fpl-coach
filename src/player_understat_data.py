"""A module for loading player match data from Understat. """
import asyncio
from typing import Any, Dict
import aiohttp
from understat import Understat
from constants import START_YEAR
from db import MySQLManager
from fixtures import fixture_id_map
from players import get_player_list
from utils import cast_float_safe

fixture_id_map = fixture_id_map()
MatchData = Dict[int, Dict[str, Dict[str, Any]]]


def update_player_match_stats(match_data: MatchData, player_id: int, match: dict) -> None:
    """Updates match_data with given player's stats."""
    ustat_id = int(match["id"])
    if ustat_id not in fixture_id_map:
        # not a premier league game
        return
    fixture_id = fixture_id_map[ustat_id]
    if fixture_id not in match_data:
        match_data[fixture_id] = {}
    if player_id not in match_data[fixture_id]:
        match_data[fixture_id][player_id] = {
            "npxG": cast_float_safe(match["npxG"]),
            "xA": cast_float_safe(match["xA"])
        }


async def get_player_understat_data() -> MatchData:
    """Fetch all player's match data from the current season."""
    players = get_player_list()
    match_data = {}
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        for player in players:
            player_ustat_id = player["understat_id"]
            if player_ustat_id is None:
                continue
            player_name = player["fpl_name"]
            try:
                matches = await understat.get_player_matches(
                    player_ustat_id, season=START_YEAR
                )
            except UnboundLocalError:
                print(
                    f"Could not fetch player data for {player_name} from Understat.")
                continue
            for match in matches:
                update_player_match_stats(match_data, player["fpl_id"], match)
        return match_data


def main():
    """Updates database with Understat data from each match. """
    db = MySQLManager()
    fixtures = db.get_fixtures()
    match_data = asyncio.run(get_player_understat_data())
    for fixture in fixtures:
        fixture_id = fixture[0]
        if not fixture_id in match_data:
            # Understat does not have data for this fixture yet
            continue
        for player_id, stats in match_data[fixture_id].items():
            db.update_row(
                "player_gws",
                {"fixture_id": fixture_id, "player_id": player_id},
                stats
            )


if __name__ == "__main__":
    main()
