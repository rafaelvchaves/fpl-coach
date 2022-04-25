"""Loads a FPL manager's complete team history."""
import requests
from constants import FPL_MANAGER_HISTORY_URL, FPL_SQUAD_URL, FPL_TRANSFERS_URL, TEAM_HISTORY_FILE
from db import MySQLManager
from players import create_player_map
from utils import to_json


def find_player_index(players, player_id):
    for i, player in enumerate(players):
        if player["id"] == player_id:
            return i
    return -1


def get_freehit_weeks(manager_id: int):
    fh_weeks = []
    chips = requests.get(
        FPL_MANAGER_HISTORY_URL.format(manager_id)).json()["chips"]
    for chip in chips:
        if chip["name"] == "freehit":
            fh_weeks.append(chip["event"])
    return fh_weeks


player_idx = create_player_map("fpl_id", None)


def get_gw1_team(manager_id: int):
    team_gw1 = requests.get(FPL_SQUAD_URL.format(
        manager_id, 1)).json()["picks"]
    team = [[]]
    for player in team_gw1:
        player_id = player["element"]
        team[0].append({
            "id": player_id,
            "name": player_idx[player_id]["fpl_name"]
        })
    return team


def get_team_history(manager_id: int):
    team = get_gw1_team(manager_id)
    fh_weeks = get_freehit_weeks(manager_id)
    transfers = requests.get(FPL_TRANSFERS_URL.format(manager_id)).json()
    last_updated = 1
    for transfer in reversed(transfers):
        in_player_id = transfer["element_in"]
        out_player_id = transfer["element_out"]
        gameweek = transfer["event"]
        while gameweek > last_updated:
            # copy team over from the last time a transfer was made
            copy_from = last_updated - 2 if last_updated in fh_weeks else last_updated - 1
            team.append(team[copy_from].copy())
            last_updated += 1
        team_this_gw = team[gameweek - 1]
        player_to_swap = find_player_index(team_this_gw, out_player_id)
        team[gameweek - 1][player_to_swap] = {
            "id": in_player_id,
            "name": player_idx[in_player_id]["fpl_name"]
        }
    # Copy team over until last gameweek
    while gameweek <= 38:
        copy_from = gameweek - 2 if gameweek in fh_weeks else gameweek - 1
        team.append(team[copy_from].copy())
        gameweek += 1

    return team


if __name__ == "__main__":
    manager_id = 505657
    team_history = get_team_history(manager_id)
    db = MySQLManager()
    db.insert_rows(
        "managers", [{"id": manager_id, "manager_name": "Rafael Chaves"}])
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
    to_json(TEAM_HISTORY_FILE, team)
