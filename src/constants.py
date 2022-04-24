from os.path import join

CURRENT_SEASON = "2021-22"
START_YEAR = CURRENT_SEASON[:-3]

# FPL API endpoints
FPL_BASE_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FPL_FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"
FPL_GAMEWEEK_URL = "https://fantasy.premierleague.com/api/event/{}/live/"
FPL_LOGIN_URL = "https://users.premierleague.com/accounts/login/"
FPL_MANAGER_HISTORY_URL = "https://fantasy.premierleague.com/api/entry/{}/history/"
FPL_MYTEAM_URL = "https://fantasy.premierleague.com/api/my-team/{}/"
FPL_PLAYER_URL = "https://fantasy.premierleague.com/api/element-summary/{}/"
FPL_SQUAD_URL = "https://fantasy.premierleague.com/api/entry/{}/event/{}/picks/"
FPL_TRANSFERS_URL = "https://fantasy.premierleague.com/api/entry/{}/transfers/"
FTE_MATCHES_URL = "https://projects.fivethirtyeight.com/soccer-api/club/spi_matches_latest.csv"

# Data files
DATA_DIR = "../data"
FIXTURES_FILE = join(DATA_DIR, "fixtures.csv")
GW_HISTORY_FILE = join(DATA_DIR, "gw_history.csv")
OPTIONS_FILE = join(DATA_DIR, "filter_options.json")
PLAYERS_FILE = join(DATA_DIR, "players_{}.json".format(CURRENT_SEASON))
RUNS_FILE = join(DATA_DIR, "runs.json")
TEAMS_FILE = join(DATA_DIR, "teams_{}.json".format(CURRENT_SEASON))
TEAM_HISTORY_FILE = join(DATA_DIR, "team_history.json")
UNDERSTAT_PLAYER_FILE = join(DATA_DIR, "understat_player_data.json")

# Model parameters
NPXG_ALPHA = 0.2
XA_ALPHA = 0.2
BONUS_ALPHA = 0.2
MINUTES_ALPHA = 0.5
