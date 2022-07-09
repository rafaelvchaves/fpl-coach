import fbref
import fplapi
import utils
import document
from constants import LAST_SEASON

class Data:

    def __init__(self, current_players):
        self.current_players = current_players

    def init_player(self, player):
        player_doc = document.Document(player)
        player_doc.retain_keys([
            "id",
            "first_name",
            "second_name",
            "web_name",
            "element_type",
            "team"
        ])
        player_doc.rename_keys({
            "id": "fpl_id",
            "team": "team_id",
            "element_type": "position"
        })
        fbref_id = fbref.get_id(player)
        player_doc.put("fbref_id", fbref_id)
        print(player["web_name"])
        seed_stats = fbref.get_season_stats(fbref_id, LAST_SEASON)
        player_doc.put("seed_stats", seed_stats)
        return player_doc.json()

    def fetch_new(self):
        current_ids = {player["fpl_id"] for player in self.current_players}
        stats = {player["fpl_id"]: player["seed_stats"]
                 for player in self.current_players}
        new_players = []
        for player in fplapi.get_players():
            if player["id"] not in current_ids or stats[player["id"]] is None:
                new_players.append(self.init_player(player))
        return new_players

    def fetch_one(self):
        current_ids = {player["fpl_id"] for player in self.current_players}
        stats = {player["fpl_id"]: player["seed_stats"]
                 for player in self.current_players}
        for player in fplapi.get_players():
            if player["id"] not in current_ids or stats[player["id"]] is None:
                yield self.init_player(player)
