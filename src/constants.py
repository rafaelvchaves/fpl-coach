from os.path import join

CURRENT_SEASON = "2021-22"

FPL_BASE_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FPL_PLAYER_URL = "https://fantasy.premierleague.com/api/element-summary/{}/"
FPL_FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"

DATA_DIR = "../data"
FIXTURES_FILE = join(DATA_DIR, "fixtures.csv")
GW_HISTORY_FILE = join(DATA_DIR, "gw_history.csv")
MERGED_DATA_FILE = join(DATA_DIR, "merged_data.csv")
PLAYERS_FILE = join(DATA_DIR, "players_{}.json".format(CURRENT_SEASON))
TEAMS_FILE = join(DATA_DIR, "teams_{}.json".format(CURRENT_SEASON))
UNDERSTAT_PLAYER_FILE = join(DATA_DIR, "understat_player_data.json")
