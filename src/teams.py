import requests
import json
import mysql.connector
import os
from constants import CURRENT_SEASON, FPL_BASE_URL, TEAMS_FILE
from utils import from_json, connect_to_db

understat_names = {
    "Man City": "Manchester City",
    "Man Utd": "Manchester United",
    "Newcastle": "Newcastle United",
    "Spurs": "Tottenham",
    "Wolves": "Wolverhampton Wanderers",
}

db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="fplcoachdb"
    )

cursor = db.cursor()

def make_team_json(team):
    team_name = team["name"]
    return {
        "id": team["id"],
        "fpl_name": team_name,
        "understat_name": understat_names.get(team_name, team_name)
    }


def get_fpl_teams(cache=False):
    """Retrieves a list of current Premier League teams.

    Returns:
      A list, with the ith entry corresponding to the team with id i.
    """
    if cache and os.path.exists(TEAMS_FILE):
        return from_json(TEAMS_FILE)
    teams_json = requests.get(FPL_BASE_URL).json()['teams']
    teams = [make_team_json(team) for team in teams_json]
    sql = "INSERT INTO teams (id, fpl_name, understat_name) VALUES ({}, '{}', '{}')"
    for team_json in teams_json:
        team = make_team_json(team_json)
        teams.append(team)
        cursor.execute(
            sql.format(team["id"], team["fpl_name"], team["understat_name"])
        )
    db.commit()
    with open(TEAMS_FILE, "w") as tj:
        json.dump(teams, tj, indent=4)
    return teams


def create_map(key_col, val_col):
    teams = get_fpl_teams()
    return {team[key_col]: team[val_col] for team in teams}


def understat_to_fpl_map():
    return create_map("understat_name", "fpl_name")


def id_to_name_map():
    return create_map("id", "fpl_name")


if __name__ == "__main__":
    get_fpl_teams()
