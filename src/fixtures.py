import aiohttp
import asyncio
import csv
import datetime
import json
import numpy as np
import os
import pandas as pd
import requests
from constants import CURRENT_SEASON, FIXTURES_FILE, FPL_FIXTURES_URL
from dateutil import parser
from functools import cmp_to_key
from teams import id_to_name_map
from teams import understat_to_fpl_map
from understat import Understat
from utils import parse_date, compare_by_index

team_map = id_to_name_map()
name_map = understat_to_fpl_map()


async def get_team_understat_data():
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


def get_xg_data(fixture, date, understat_team_data):
    today = datetime.date.today().strftime("%Y-%m-%d")
    home_team = team_map[fixture["team_h"]]
    away_team = team_map[fixture["team_a"]]
    if date is not None and date < today:
        if home_team in understat_team_data[date]:
            home_xg = understat_team_data[date][home_team]["xG"]
            away_xg = understat_team_data[date][away_team]["xG"]
            return round(home_xg, 3), round(away_xg, 3)
    return None, None


def get_fixture_info(fixture, understat_team_data):
    fixture_id = fixture["id"]
    gw = fixture["event"]
    home_team = team_map[fixture["team_h"]]
    home_score = fixture["team_h_score"]
    away_score = fixture["team_a_score"]
    away_team = team_map[fixture["team_a"]]
    date = parse_date(fixture["kickoff_time"])
    home_xg, away_xg = get_xg_data(fixture, date, understat_team_data)
    return [
        fixture_id,
        gw,
        date,
        home_team,
        home_score,
        away_score,
        away_team,
        home_xg,
        away_xg
    ]


def get_fixtures():
    f = open(FIXTURES_FILE, "w")
    writer = csv.writer(f)
    header = ["fixture_id", "gw", "date", "home_team",
              "home_score", "away_score", "away_team", "home_xg", "away_xg"]
    writer.writerow(header)
    print("Getting fixtures...")
    fixtures_json = requests.get(FPL_FIXTURES_URL).json()
    understat_team_data = asyncio.run(get_team_understat_data())
    rows = [get_fixture_info(fj, understat_team_data) for fj in fixtures_json]
    rows.sort(key=compare_by_index(1))
    writer.writerows(rows)
    print("Done")
    f.close()


if __name__ == "__main__":
    get_fixtures()
