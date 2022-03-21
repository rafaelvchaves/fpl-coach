import aiohttp
import asyncio
import json
import os
import requests
import unidecode
from constants import CURRENT_SEASON, FPL_BASE_URL, PLAYERS_FILE
from teams import id_to_name_map
from understat import Understat
from utils import from_json

def get_position(element_type):
    if element_type == 1:
        return "G"
    elif element_type == 2:
        return "D"
    elif element_type == 3:
        return "M"
    else:
        return "F"

def get_fpl_players():
    """Retrieves a dictionary of all FPL players in current season.

    Returns:
      A dict, mapping a player's name with all accent marks stripped, to another
      dictionary in the following format:
      {
        "name": the name of the player (with accents) as given by FPL.
        "fpl_id": the player's id for the current season.
        "team_name": the name of the team that the player plays for
      }
    """
    players_json = requests.get(FPL_BASE_URL).json()["elements"]
    pmap = {}
    tmap = id_to_name_map()
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

    Raises:
      FileNotFoundError: There is no file "aliases.json" in the "data/"
      directory.
    """
    with open("data/aliases.json") as alias_json:
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
        print("uid {} cannot be converted to int".format(uid))
        exit()
    return {
        "fpl_id": pmap[name]["fpl_id"],
        "understat_id": understat_id,
        "name": pmap[name]["name"],
        "team_name": pmap[name]["team_name"],
        "position": pmap[name]["position"]
    }


async def generate_player_list(output_file_path):
    """
      Writes a complete list of FPL players to output_file_path.

    The list is comprised of json objects with the following structure:
      {
        "fpl_id": player's FPL ID
        "understat_id":  player's Understat ID
        "name": player's name, as given on FPL
        "team_name": name of team that player plays for
      }

    Raises:
      Exception: At least one (FPL name, Understat name) match was not found.
    """
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        ust_players = await understat.get_league_players(
            "epl",
            CURRENT_SEASON[:-3]
        )
        pmap = get_fpl_players()
        aliases = get_aliases()
        not_found = []
        players = []
        print("Fetching players from Understat...")
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
        raise Exception(err_msg)
    print("Done")
    with open(output_file_path, "w") as f:
        json.dump(players, f, indent=4, ensure_ascii=False)
    return players

def get_player_list():
    # check cache
    if os.path.exists(PLAYERS_FILE):
        return from_json(PLAYERS_FILE)
    return generate_player_list(PLAYERS_FILE)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(generate_player_list(PLAYERS_FILE))
