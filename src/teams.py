"""A module for loading static team data from FPL, Understat, and
FiveThirtyEight. """
import requests
from constants import FPL_BASE_URL, TEAMS_FILE
from utils import from_json, to_json
from db import MySQLManager

understat_names = {
    "Man City": "Manchester City",
    "Man Utd": "Manchester United",
    "Newcastle": "Newcastle United",
    "Spurs": "Tottenham",
    "Wolves": "Wolverhampton Wanderers",
}

fte_names = {
    "Man City": "Manchester City",
    "Man Utd": "Manchester United",
    "Spurs": "Tottenham Hotspur",
    "Wolves": "Wolverhampton",
    "Brighton": "Brighton and Hove Albion",
    "West Ham": "West Ham United",
    "Leicester": "Leicester City",
    "Leeds": "Leeds United",
    "Norwich": "Norwich City"
}


def make_team_json(team: dict) -> dict:
    """Creates a team json.

    Args:
        team: A dictionary containing fields for the FPL name and ID of the team.
    Returns:
        A dictionary with the following keys:
            fpl_id: The FPL ID of the team for the current season.
            fpl_name: The name of the team, as listed on FPL.
            understat_name: The name of the team, as listed on Understat.
            fte_name: The name of the team, as listed on FiveThirtyEight.
    """
    team_name = team["name"]
    return {
        "fpl_id": team["id"],
        "fpl_name": team_name,
        "understat_name": understat_names.get(team_name, team_name),
        "fte_name": fte_names.get(team_name, team_name)
    }


def get_fpl_teams(cache=True):
    """Retrieves a list of current Premier League teams.

    Args:
        cache: Whether to load the data from a file cache rather than calling
          the FPL API. Defaults to True.

    Returns:
      A list of dictionaries, with fields specified in make_team_json.
    """
    if cache:
        return from_json(TEAMS_FILE)
    teams_json = requests.get(FPL_BASE_URL).json()["teams"]
    teams = [make_team_json(team) for team in teams_json]
    to_json(TEAMS_FILE, teams)
    return teams


def create_team_map(key_col: str, val_col: str):
    """Returns a dictionary from key_col to val_col.

    The options for key_col and val_col are 'fpl_id', 'fpl_name',
    'understat_name', and 'fte_name'."""
    return {team[key_col]: team[val_col] for team in get_fpl_teams()}


if __name__ == "__main__":
    db = MySQLManager()
    team_rows = get_fpl_teams()
    db.insert_rows("teams", team_rows)
