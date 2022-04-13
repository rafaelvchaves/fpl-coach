import aiohttp
import asyncio
import json
import os
import requests
import unidecode
from constants import START_YEAR, FPL_BASE_URL, PLAYERS_FILE, DATA_DIR
from teams import create_map
from db import MySQLManager
from understat import Understat
from utils import *


def get_position(element_type):
    return {
        1: "G",
        2: "D",
        3: "M",
        4: "F"
    }[element_type]


def get_fpl_players():
    """Retrieves a dictionary of all FPL players in current season.

    Returns:
      A dict, mapping a player's name with all accent marks stripped, to another
      dictionary in the following format:
      {
        "name": the name of the player (with accents) as given by FPL.
        "fpl_id": the player's id for the current season.
        "team_name": the name of the team that the player plays for.
        "position": the player's position listed on FPL.
      }
    """
    players_json = requests.get(FPL_BASE_URL).json()["elements"]
    pmap = {}
    tmap = create_map("fpl_id", "fpl_name")
    for p in players_json:
        player_name = p["first_name"] + " " + p["second_name"]
        candidate_names = [
            player_name,
            p["web_name"],
            p["first_name"] + " " + p["web_name"],
            p["first_name"].split()[0] + " " + p["second_name"].split()[-1]
        ]
        for name in candidate_names:
            pmap[unidecode.unidecode(name)] = {
                "name": player_name,
                "fpl_id": p["id"],
                "team_name": tmap[p["team"]],
                "position": get_position(p["element_type"])
            }
    return pmap


def get_aliases():
    """Gets name conversions between Understat names and FPL names.

    Aliases are hard-coded and retrieved from "data/aliases.json".

    Returns:
      A dict mapping a player's Understat name to their FPL name.
    """
    with open(os.path.join(DATA_DIR, "aliases.json")) as alias_json:
        return json.load(alias_json)


def clean_name(aliases, name):
    """Cleans a player name to be utilized in the players map.

    Strips accent marks and gets alias from aliases, if applicable.
    """
    cleaned_name = name.replace("&#039;", "'")
    cleaned_name = aliases.get(cleaned_name, cleaned_name)
    cleaned_name = unidecode.unidecode(cleaned_name)
    return cleaned_name


def construct_player_json(pmap, name, uid):
    try:
        understat_id = int(uid)
    except:
        print("understat id {} cannot be converted to int".format(uid))
        exit(1)
    return {
        "fpl_id": pmap[name]["fpl_id"],
        "understat_id": understat_id,
        "fpl_name": pmap[name]["name"],
        "team_name": pmap[name]["team_name"],
        "position": pmap[name]["position"]
    }


async def generate_player_list(output_file_path):
    """Writes a complete list of FPL players to output_file_path. """
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        ust_players = await understat.get_league_players(
            "epl",
            START_YEAR
        )
        pmap = get_fpl_players()
        aliases = get_aliases()
        not_found = []
        players = []
        for player in ust_players:
            understat_name = player["player_name"]
            player_name = clean_name(aliases, understat_name)
            uid = player["id"]
            try:
                cleaned_name = clean_name(aliases, understat_name)
                player_json = construct_player_json(pmap, cleaned_name, uid)
                players.append(player_json)
            except KeyError:
                not_found.append(player["player_name"])
    if not_found != []:
        err_msg = "Error: matches not found for following players: {}".format(
            not_found)
        print(err_msg)
        exit(1)
    to_json(PLAYERS_FILE, players)
    return players


def get_player_list():
    # check cache
    if os.path.exists(PLAYERS_FILE):
        return from_json(PLAYERS_FILE)
    return generate_player_list(PLAYERS_FILE)


def uid_to_fpl_name():
    players = get_player_list()
    return {player["understat_id"]: player["fpl_name"] for player in players}


if __name__ == "__main__":
    db = MySQLManager()
    players = asyncio.run(generate_player_list(PLAYERS_FILE))
    db.insert_rows("players", players)
