import requests
import json
import mysql.connector
import os
from constants import CURRENT_SEASON, FPL_BASE_URL, TEAMS_FILE
from utils import from_json
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


def make_team_json(team):
    team_name = team["name"]
    return {
        "fpl_id": team["id"],
        "fpl_name": team_name,
        "understat_name": understat_names.get(team_name, team_name),
        "fte_name": fte_names.get(team_name, team_name)
    }


def get_fpl_teams(cache=False):
    """Retrieves a list of current Premier League teams.

    Returns:
      A list, with the ith entry corresponding to the team with id i.
    """
    teams_json = requests.get(FPL_BASE_URL).json()['teams']
    teams = [make_team_json(team) for team in teams_json]
    return teams


def create_map(key_col, val_col):
    teams = get_fpl_teams()
    return {team[key_col]: team[val_col] for team in teams}


if __name__ == "__main__":
    db = MySQLManager()
    teams = get_fpl_teams()
    db.insert_rows("teams", teams)
