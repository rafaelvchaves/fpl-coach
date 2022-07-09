class Data:
    # map from fpl player id to:
    # completed: [...]
    # upcoming: [...]
    # match_data = {}
    # metadata = {}

    # alpha value for EMA
    # alphas = {}

    # fields = []

    def __init__(self, state):
        # state data is fetched from database
        pass

    def fetch_new(self):
        # fetches match data up to a given gameweek.

        # check if EMA from table metadata differs from EMA in constants.py, and if so,
        # recompute before adding any additional entries

        # also record last gw update in table metadata

        # metadata: {
        #   last_gw_updated: 23
        #   ema_params: {...}
        # }
        # players: {
        #   1: {
        #     name: ...
        #     ...
        #     completed: {}
        #     upcoming: {gw: 1, ..., }

        #   }
        # }

        # call fixtures.py to get new upcoming fixtures for each team in a map
        # from team id to [{fixture_id, }, ...]

        # how to find last gameweek updated? - store in metadata

        # call fpl API for each gameweek from last_updated + 1 to gameweek
        # for gw in range(metadata.last_updated + 1, gameweek + 1):
        # data = fplapi(...)
        # if elements is empty, return error?
        # for player in data["elements"]:
          # - populate stats from FPL
          # - call fbref.get_match_stats(fpl_player_id, fpl_fixture_id)
          # if this fails, probably return error
          # - merge dictionaries
          # - compute EMA
          # match_data[player["id"]]["completed"].append(data)
          # match_data[player["id"]]["upcoming"] = get_upcoming(player["team_id"])
        # 

        # return map
        pass
