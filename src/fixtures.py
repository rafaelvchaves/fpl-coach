import aiohttp
import asyncio
import csv
import datetime
import json
import requests
from constants import CURRENT_SEASON, FIXTURES_FILE, FPL_FIXTURES_URL
from dateutil import parser
from functools import cmp_to_key
from teams import id_to_name_map
from teams import understat_to_fpl_map
from typing import Optional
from understat import Understat
from utils import parse_date, compare_by_index
from db import MySQLManager

team_map = id_to_name_map()
name_map = understat_to_fpl_map()

async def get_team_understat_data():
    """Retrieves Understat data from all teams in the current season.

    Returns:
        A dictionary with dates as keys, which map to a dictionary of teams that
        played that day and their corresponding statistics in that fixture. For
        example,
        {
            "2021-08-13": {
                "Arsenal": {
                    "xG": 1.024,
                    "xGA": 1.888
                },
                ...
            },
            ....
        }
    """
    async with aiohttp.ClientSession() as session:
        fixture_map = {}
        understat = Understat(session)
        teams = await understat.get_teams("epl", CURRENT_SEASON[:-3])
        for team in teams:
            for game in team["history"]:
                date = parse_date(game["date"])
                team_name = name_map[team["title"]]
                if date not in fixture_map:
                    fixture_map[date] = {}
                if team_name not in fixture_map[date]:
                    fixture_map[date][team_name] = {
                        "xG": float(game["xG"]),
                        "xGA": float(game["xGA"])
                    }
        return fixture_map

understat_team_data = asyncio.run(get_team_understat_data())

def get_xG_data(fixture: dict, date : Optional[str]):
    """Get the xG of the home and away team in a certain fixture.

    Returns:
        A tuple (hxG, axG), where hxG is the home team's xG and axG is the
        away team's xG for that fixture, if this fixture has occurred.
        (None, None) otherwise.
    """
    today = datetime.date.today().strftime("%Y-%m-%d")
    if date is not None and date < today:
        match_data = understat_team_data[date]
        home_team = team_map[fixture["team_h"]]
        away_team = team_map[fixture["team_a"]]
        if home_team in match_data:
            home_xG = match_data[home_team]["xG"]
            away_xG = match_data[away_team]["xG"]
            return round(home_xG, 3), round(away_xG, 3)
    return None, None


def get_fixture_info(fixture : dict) -> dict:
    """Extract data from a fixture json."""
    date = parse_date(fixture["kickoff_time"])
    home_xG, away_xG = get_xG_data(fixture, date, understat_team_data)
    return {
        "id": fixture["id"],
        "gameweek": fixture["event"],
        "kickoff_date": date,
        "home_team": team_map[fixture["team_h"]],
        "home_score": fixture["team_h_score"],
        "away_score": fixture["team_a_score"],
        "away_team": team_map[fixture["team_a"]],
        "home_xG": home_xG,
        "away_xG": away_xG
    }

def get_fixtures():
    """Writes fixture data to csv file.
    
    First, all of the fixtures are retrieved from the FPL API, and then each
    fixture is populated with the corresponding Understat xG data, if possible.
    """
    print("Getting fixtures...")
    fixtures_json = requests.get(FPL_FIXTURES_URL).json()
    rows = [get_fixture_info(fj, understat_team_data) for fj in fixtures_json]
    print("Done")
    return rows


if __name__ == "__main__":
    db = MySQLManager()
    fixtures = get_fixtures()
    db.writerows(fixtures, "fixtures")
