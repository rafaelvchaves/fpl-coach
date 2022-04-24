"""Loads a FPL manager's complete team history."""
import requests
from constants import FPL_SQUAD_URL
from players import get_player_index

player_idx = get_player_index()
team_gw1 = requests.get(FPL_SQUAD_URL.format(505657, 1)).json()["picks"]
team = {}
for player in team_gw1:
    player_id = player["element"]
    position = player_idx[player_id]["position"]
    if not position in team:
        team[position] = [[]]
    name = player_idx[player_id]["fpl_name"]
    team[position][0].append(name)

print(team)
