"""A module for loading player gameweek data from FPL. """
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from functools import partial
import requests
from constants import FPL_GAMEWEEK_URL
from db import MySQLManager
from players import create_player_map, fetch_players
from utils import get_current_gw, get_gw_range, mapl, subset_dict, Rows

desired_stats = {
    "minutes", "goals_scored", "assists", "clean_sheets", "goals_conceded",
    "bonus", "saves"
}
get_name = create_player_map("fpl_id", "fpl_name")
get_team = create_player_map("fpl_id", "team_name")


def get_stat_map(stats: List[dict]) -> Callable[[str], int]:
    """Returns a function that takes in a stat name and outputs its value."""
    stat_dict = {"total_points": 0}
    for stat in stats:
        stat_dict["total_points"] += stat["points"]
        stat_dict[stat["identifier"]] = stat["value"]
    return lambda s: stat_dict.get(s, 0)


def get_match_data(
    player_id: int,
    team: str,
    fixture_id: int,
    stat_lookup: Callable[[str], Optional[int]] = lambda s: 0
) -> Dict[str, Any]:
    """Returns a dictionary containing a player's id, the fixture id, the
    team the player plays for, and their stats in the fixture."""
    return {
        "player_id": player_id,
        "fixture_id": fixture_id,
        "team": team,
        **{stat: stat_lookup(stat) for stat in desired_stats},
        "total_points": stat_lookup("total_points")
    }


def get_remaining_fixture_ids(db: MySQLManager()) -> Dict[str, List[int]]:
    """Gets a dictionary of each team's remaining fixtures for the current
    season.

    Args:
        db: A MySQLManager instance to load team gameweeek data from.

    Returns:
        A dictionary, mapping a team name to a list of fixture ids that they
          remain to play.
    """
    remaining_fixtures = {}
    team_fixtures = db.exec_query(
        f"SELECT team, fixture_id FROM team_gws WHERE gameweek > {get_current_gw()}")
    for team, fixture_id in team_fixtures:
        if not team in remaining_fixtures:
            remaining_fixtures[team] = [fixture_id]
        else:
            remaining_fixtures[team].append(fixture_id)
    return remaining_fixtures


def get_player_gw_data(player: dict, remaining_fixtures: Dict[str, List[int]]) -> Tuple[Rows, Rows]:
    """Gets a list of match data for specified player over the season.

    Args:
        player: A dictionary where the player data is extracted from.
        remaining_fixtures: Upcoming fixtures to add blank entries.

    Returns:
        A tuple of rows, the first of which is static player info and the second
        is the player's gameweek history.
    """
    gw_data = []
    player_id = player["id"]
    team = get_team[player_id]
    matches = player["explain"]
    for match in matches:
        fixture_id = match["fixture"]
        if player["stats"]["minutes"] == 0:
            player_match_data = get_match_data(player_id, team, fixture_id)
        else:
            stat_lookup = get_stat_map(match["stats"])
            player_match_data = get_match_data(
                player_id, team, fixture_id, stat_lookup)
        gw_data.append(player_match_data)
    # also add empty entries for upcoming games, if any.
    if team in remaining_fixtures:
        for fixture_id in remaining_fixtures[team]:
            gw_data.append(get_match_data(
                player_id, team, fixture_id, lambda s: None))
    extract_info = partial(subset_dict, keys=["player_id", "fixture_id"])
    basic_info = mapl(extract_info, gw_data)
    return basic_info, gw_data


def write_gw_data(db: MySQLManager, gws: Optional[Union[int, Tuple[int]]] = None) -> None:
    """Writes all player match data from the specified gws.

    Args:
        gws: An int representing a single gameweek to get data from, or a tuple
          (start, end), indicating to get data from the gameweek [start] to
          [end], inclusive. If gws is None, then all gameweek data since
          gameweek 1 will be written.
    """
    remaining_fixtures = get_remaining_fixture_ids(db)
    start, end = get_gw_range(gws)
    for gw in range(start, end + 1):
        gw_url = FPL_GAMEWEEK_URL.format(gw)
        gw_data = requests.get(gw_url).json()["elements"]
        for player in gw_data:
            info, gw_data = get_player_gw_data(player, remaining_fixtures)
            db.insert_rows("player_gws", gw_data)
            db.insert_rows("player_gws_predicted", info)


def main():
    """Updates player FPL data for all gameweeks."""
    db = MySQLManager()
    write_gw_data(db)


if __name__ == "__main__":
    main()
