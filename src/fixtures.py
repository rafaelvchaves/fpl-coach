import aiohttp
import asyncio
import numpy as np
import requests
from constants import CURRENT_SEASON, FPL_FIXTURES_URL
from teams import id_to_name_map, understat_to_fpl_map
from understat import Understat
from utils import *
from db import MySQLManager
from teams import get_fpl_teams

id_to_name = id_to_name_map()
ustat_to_fpl = understat_to_fpl_map()


def add_fixture(fixture_map, fixture):
    home_team = ustat_to_fpl[fixture["h"]["title"]]
    away_team = ustat_to_fpl[fixture["a"]["title"]]
    if not home_team in fixture_map:
        fixture_map[home_team] = {}
    fixture_map[home_team][away_team] = {
        "fpl_id": None,
        "understat_id": cast_int_safe(fixture["id"]),
        "gameweek": None,
        "kickoff_date": None,
        "completed": None,
        "home_team": home_team,
        "home_score": cast_int_safe(fixture["goals"]["h"]),
        "away_score": cast_int_safe(fixture["goals"]["a"]),
        "away_team": away_team,
        "home_xG": cast_float_safe(fixture["xG"]["h"]),
        "away_xG": cast_float_safe(fixture["xG"]["a"])
    }


async def get_understat_fixture_data():
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        old_fixtures = await understat.get_league_results("epl", CURRENT_SEASON[:-3])
        new_fixtures = await understat.get_league_fixtures("epl", CURRENT_SEASON[:-3])
        old_fixtures.extend(new_fixtures)
        fixture_map = {}
        for fixture in old_fixtures:
            add_fixture(fixture_map, fixture)
        return fixture_map


def create_team_gw_row(fixture, home):
    return {
        "gameweek": fixture["gameweek"],
        "fixture_id": fixture["fpl_id"],
        "kickoff_date": fixture["kickoff_date"],
        "completed": fixture["completed"],
        "team": fixture["home_team"] if home else fixture["away_team"],
        "opponent": fixture["away_team"] if home else fixture["home_team"],
        "home": home,
        "team_xG": fixture["home_xG"] if home else fixture["away_xG"],
        "team_xGA": fixture["away_xG"] if home else fixture["home_xG"]
    }


def get_team_gws(fixtures):
    rows = []
    for fixture in fixtures:
        rows.append(create_team_gw_row(fixture, True))
        rows.append(create_team_gw_row(fixture, False))
    return rows


def get_fixtures():
    fpl_fixtures = requests.get(FPL_FIXTURES_URL).json()
    understat_fixture_data = asyncio.run(get_understat_fixture_data())
    rows = []
    for fixture in fpl_fixtures:
        # Fill in data from FPL
        home_team = id_to_name[fixture["team_h"]]
        away_team = id_to_name[fixture["team_a"]]
        row = understat_fixture_data[home_team][away_team]
        row["fpl_id"] = fixture["id"]
        row["gameweek"] = fixture["event"]
        row["kickoff_date"] = parse_date(fixture["kickoff_time"])
        row["completed"] = fixture["finished"]
        rows.append(row)
    return rows


def get_ema(df, team, col):
    new_col = "ema_" + col
    ema = df[df["team"] == team][col].ewm(alpha=0.2).mean()
    ema = ema.to_numpy()
    ema = np.roll(ema, 1)
    ema[0] = None
    ema = np.round(ema, 3)
    return ema


def compute_averages(db):
    teams = get_fpl_teams()
    for team in teams:
        team_name = team["fpl_name"]
        query = """SELECT * FROM team_gws
        WHERE gameweek IS NOT NULL
        ORDER BY kickoff_date"""
        df = db.get_df(query)
        xg = get_ema(df, team_name, "team_xG")
        xga = get_ema(df, team_name, "team_xGA")
        team_df = df[df["team"] == team_name].reset_index()
        for i, r in team_df.iterrows():
            db.update_row(
                "team_gws",
                {"fixture_id": r["fixture_id"], "team": team_name},
                {"avg_team_xG": xg[i], "avg_team_xGA": xga[i]}
            )


if __name__ == "__main__":
    db = MySQLManager()
    fixtures = get_fixtures()
    db.insert_rows("fixtures", fixtures)
    team_gws = get_team_gws(fixtures)
    db.insert_rows("team_gws", team_gws)
    compute_averages(db)
