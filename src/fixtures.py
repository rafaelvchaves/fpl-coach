import aiohttp
import asyncio
import requests
from constants import CURRENT_SEASON, FPL_FIXTURES_URL
from teams import id_to_name_map, understat_to_fpl_map
from understat import Understat
from utils import *
from db import MySQLManager

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
        "kickoff_date": parse_date(fixture["datetime"]),
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
        home_team = id_to_name[fixture["team_h"]]
        away_team = id_to_name[fixture["team_a"]]
        row = understat_fixture_data[home_team][away_team]
        row["fpl_id"] = fixture["id"]
        row["gameweek"] = fixture["event"]
        rows.append(row)
    return rows


if __name__ == "__main__":
    db = MySQLManager()
    fixtures = get_fixtures()
    db.writerows(fixtures, "fixtures")
    team_gws = get_team_gws(fixtures)
    db.writerows(team_gws, "team_gws")
