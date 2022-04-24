"""Loads a FPL manager's complete team history."""
import requests
from constants import FPL_MANAGER_HISTORY_URL, FPL_SQUAD_URL, FPL_TRANSFERS_URL, TEAM_HISTORY_FILE
from players import create_player_map
from utils import to_json


def find_player_index(players, player_id):
    for i, player in enumerate(players):
        if player["id"] == player_id:
            return i
    return -1


def get_freehit_weeks():
    fh_weeks = []
    chips = requests.get(
        FPL_MANAGER_HISTORY_URL.format(team_id)).json()["chips"]
    for chip in chips:
        if chip["name"] == "freehit":
            fh_weeks.append(chip["event"])
    return fh_weeks


team_id = 505657
player_idx = create_player_map("fpl_id", None)
fh_weeks = get_freehit_weeks()


def get_gw1_team():
    team_gw1 = requests.get(FPL_SQUAD_URL.format(team_id, 1)).json()["picks"]
    team = [{"G": [], "D": [], "M": [], "F": []}]
    for player in team_gw1:
        player_id = player["element"]
        position = player_idx[player_id]["position"]
        team[0][position].append({
            "id": player_id,
            "name": player_idx[player_id]["fpl_name"]
        })
    return team


def get_team_history():
    team = get_gw1_team()
    transfers = requests.get(FPL_TRANSFERS_URL.format(team_id)).json()
    last_updated = 1
    for transfer in reversed(transfers):
        in_player_id = transfer["element_in"]
        out_player_id = transfer["element_out"]
        position = player_idx[out_player_id]["position"]
        transfer_gameweek = transfer["event"]
        while transfer_gameweek > last_updated:
            # copy team over from the last time a transfer was made
            copy_from = last_updated - 2 if last_updated in fh_weeks else last_updated - 1
            team.append(
                {p: team[copy_from][p].copy() for p in ["G", "D", "M", "F"]}
            )
            last_updated += 1
        team_at_pos = team[transfer_gameweek - 1][position]
        player_to_swap = find_player_index(team_at_pos, out_player_id)
        team[transfer_gameweek - 1][position][player_to_swap] = {
            "id": in_player_id,
            "name": player_idx[in_player_id]["fpl_name"]
        }
    return team


if __name__ == "__main__":
    team = get_team_history()
    to_json(TEAM_HISTORY_FILE, team)
