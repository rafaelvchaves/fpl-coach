"""Loads a FPL manager's complete team history."""
from typing import List
import requests
from constants import (
    FPL_MANAGER_HISTORY_URL,
    FPL_SQUAD_URL,
    FPL_TRANSFERS_URL,
    TEAM_HISTORY_FILE
)
from db import MySQLManager
from players import create_player_map
from utils import to_json


def find_player_index(players: List[dict], player_id: int) -> int:
    """Returns the index i in players that has id player_id. -1 if none."""
    for i, player in enumerate(players):
        if player["id"] == player_id:
            return i
    return -1


def get_freehit_weeks(manager_id: int) -> List[int]:
    """Returns a list of gameweeks that this manager played the Free Hit chip. """
    fh_weeks = []
    chips = requests.get(
        FPL_MANAGER_HISTORY_URL.format(manager_id)).json()["chips"]
    for chip in chips:
        if chip["name"] == "freehit":
            fh_weeks.append(chip["event"])
    return fh_weeks


player_idx = create_player_map("fpl_id", None)


def get_gw1_team(manager_id: int) -> List[List[dict]]:
    """Gets manager's team in gameweek 1.

    Args:
        manager_id: The FPL ID of the manager.

    Returns:
        A list with a single element, which is a list of players
        in the gameweek 1 team.
    """
    gw1_team = requests.get(FPL_SQUAD_URL.format(
        manager_id, 1)).json()["picks"]
    team = [[]]
    for player in gw1_team:
        player_id = player["element"]
        team[0].append({
            "id": player_id,
            "name": player_idx[player_id]["fpl_name"]
        })
    return team


def get_team_history(manager_id: int) -> List[List[dict]]:
    """Gets a manager's full team history.

    Args:
        manager_id: The FPL ID of the manager.

    Returns:
        A list of length 38 (one entry for each gameweek). Each
        entry in the list is another list of dictionaries, representing
        the 15 players that were on the manager's team that week.
        For future gameweeks, the last non free hit team is copied over.
    """
    team = get_gw1_team(manager_id)
    fh_weeks = get_freehit_weeks(manager_id)
    transfers = requests.get(FPL_TRANSFERS_URL.format(manager_id)).json()
    last_updated = 1

    def latest_team_idx(gw):
        return gw - 2 if gw in fh_weeks else gw - 1

    gameweek = 2
    for transfer in reversed(transfers):
        in_player_id = transfer["element_in"]
        out_player_id = transfer["element_out"]
        gameweek = transfer["event"]
        while gameweek > last_updated:
            # copy team over from the last time a transfer was made
            team.append(team[latest_team_idx(last_updated)].copy())
            last_updated += 1
        player_to_swap = find_player_index(team[gameweek - 1], out_player_id)
        team[gameweek - 1][player_to_swap] = {
            "id": in_player_id,
            "name": player_idx[in_player_id]["fpl_name"]
        }
    # Copy team over until last gameweek
    while gameweek <= 38:
        team.append(team[latest_team_idx(gameweek)].copy())
        gameweek += 1
    return team


def main(manager_id: int, manager_name: str):
    """Adds a manager's complete team history to the database."""
    team_history = get_team_history(manager_id)
    db = MySQLManager()
    db.insert_rows(
        "managers", [{"id": manager_id, "manager_name": manager_name}])
    rows = []
    for i, team in enumerate(team_history):
        gw = i + 1
        for player in team:
            rows.append({
                "gameweek": gw,
                "manager_id": manager_id,
                "player_id": player["id"]
            })
    db.insert_rows("manager_gws", rows)
    to_json(TEAM_HISTORY_FILE, team_history)


if __name__ == "__main__":
    main(505657, "Rafael Chaves")
