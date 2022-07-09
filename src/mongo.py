from pymongo import MongoClient
import player
import os


class Handler:

    def __init__(self):
        password = os.environ.get("FPLCOACH_PASSWORD")
        self.client = MongoClient(
            f"mongodb+srv://fplcoach-admin:{password}@cluster0.z88di.mongodb.net/?retryWrites=true&w=majority")
        self.players_collection = self.client.fplcoachdb.players
        self.matches_collection = self.client.fplcoachdb.matches

    def get_match_state(self):
        pass

    def update_players(self):
        current_players = list(self.players_collection.find({}))
        pd = player.Data(current_players)
        new_players = pd.fetch_new()
        if len(new_players) > 0:
          self.players_collection.insert_many(new_players)

    def update_matches(self):
        pass
