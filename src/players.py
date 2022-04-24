"""A module for loading static player data from FPL and Understat. """
import asyncio
import os
from typing import Optional
import aiohttp
import requests
import unidecode
from understat import Understat

from constants import START_YEAR, FPL_BASE_URL, PLAYERS_FILE, DATA_DIR
from teams import create_team_map
from db import MySQLManager
from utils import cast_int_safe, from_json, mapl, to_json


def get_position(element_type: int) -> str:
    """Converts an FPL position number to a single-character string."""
    return {
        1: "G",
        2: "D",
        3: "M",
        4: "F"
    }[element_type]


def get_fpl_player_list():
    """Retrieves a list of all FPL players in current season."""
    players_json = requests.get(FPL_BASE_URL).json()["elements"]
    player_list = []
    get_team = create_team_map("fpl_id", "fpl_name")
    for player in players_json:
        first_name = player["first_name"]
        second_name = player["second_name"]
        web_name = player["web_name"]
        player_name = first_name + " " + second_name
        candidate_names = [
            player_name,
            web_name,
            first_name + " " + web_name,
            first_name.split()[0] + " " + second_name.split()[-1]
        ]
        player_list.append({
            "candidate_names": mapl(unidecode.unidecode, candidate_names),
            "name": player_name,
            "fpl_id": player["id"],
            "team_name": get_team[player["team"]],
            "position": get_position(player["element_type"])
        })
    return player_list


def hardcoded_conversions():
    """Gets hard-coded conversions from FPL to Understat IDs.

    Conversions are retrieved from "data/id_conversions.json".

    Returns:
      A dictionary mapping a subset of players' FPL ID to their Understat ID.
    """
    conv = from_json(os.path.join(DATA_DIR, "id_conversions.json"))
    return {int(k): v for k, v in conv.items()}


def clean_name(name):
    """Cleans a player name to be utilized in the players map."""
    cleaned_name = name.replace("&#039;", "'")
    cleaned_name = unidecode.unidecode(cleaned_name)
    return cleaned_name


async def get_ustat_players():
    """Retrieves list of players from understat."""
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        ustat_players = await understat.get_league_players(
            "epl",
            START_YEAR
        )
        ustat_player_map = {}
        for player in ustat_players:
            player_name = clean_name(player["player_name"])
            ustat_player_map[player_name] = player["id"]
        return ustat_player_map


def make_player_json(player, ustat_id):
    """Creates a player json.

    Returns:
        A json containing the following fields:
            fpl_id: The player's FPL ID for the current season.
            understat_id: The player's ID on understat.com
            fpl_name: The player's name, as listed in FPL.
            team_name: The name of the team that the player currently plays on.
            position: A string representing the player's position.
    """
    return {
        "fpl_id": player["fpl_id"],
        "understat_id": cast_int_safe(ustat_id),
        "fpl_name": player["name"],
        "team_name": player["team_name"],
        "position": player["position"]
    }


def get_player_list(cache=True):
    """Retrieves a list of all players in FPL for the current season.

    Args:
        cache: Whether to load the data from a file cache rather than calling
          the FPL API. Defaults to True.

    Returns:
        A list of dictionaries, with the same keys as specified in
        get_player_json.
    """
    if cache:
        return from_json(PLAYERS_FILE)
    fpl_player_list = get_fpl_player_list()
    ustat_player_map = asyncio.run(get_ustat_players())
    hardcoded_ids = hardcoded_conversions()
    players = []
    for player in fpl_player_list:
        fpl_id = player["fpl_id"]
        if fpl_id in hardcoded_ids:
            players.append(
                make_player_json(player, hardcoded_ids[fpl_id])
            )
            continue
        ustat_id = None
        for name in player["candidate_names"]:
            if name in ustat_player_map:
                ustat_id = ustat_player_map[name]
                break
        players.append(make_player_json(player, ustat_id))
    to_json(PLAYERS_FILE, players)
    return players


def create_player_map(key_col: str, val_col: Optional[str]):
    """Returns a dictionary from key_col to val_col.

    The options for key_col are 'fpl_id', 'understat_id', 'fpl_name', and the
    options for val_col are 'fpl_id', 'understat_id', 'fpl_name', 'team_name',
    'position', and None. If val_col is None, the values of the dictionary
    are the entire player jsons."""
    if val_col is None:
        return {player["fpl_id"]: player for player in get_player_list()}
    return {player[key_col]: player[val_col] for player in get_player_list()}


if __name__ == "__main__":
    db = MySQLManager()
    player_rows = get_player_list(cache=False)
    db.insert_rows("players", player_rows)
