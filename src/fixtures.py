import aiohttp
import asyncio
import pandas as pd
import requests
from constants import CURRENT_SEASON, FPL_FIXTURES_URL, FTE_MATCHES_URL
from teams import create_map
from understat import Understat
from utils import *
from db import MySQLManager
from teams import get_fpl_teams
from typing import *

id_to_name = create_map("fpl_id", "fpl_name")
ustat_to_fpl = create_map("understat_name", "fpl_name")
fpl_to_fte = create_map("fpl_name", "fte_name")

Rows = List[Dict[str, Any]]


def get_fte_df() -> pd.DataFrame:
    """Retrieves data from FiveThirtyEight's SPI csv as a pandas DataFrame."""
    df = pd.read_csv(FTE_MATCHES_URL)
    df = df[(df["league"] == "Barclays Premier League")
            & (df["season"] == 2021)]
    cols = ["date", "team1", "team2", "proj_score1",
            "proj_score2", "score1", "score2", "xg1", "xg2"]
    return df[cols]


df_fte = get_fte_df()


def find_col(fixture: Dict[str, Any], col: str, home: bool) -> Any:
    return fixture["home_" + col if home else "away_" + col]


def create_team_gw_row(fixture: Dict[str, Any], home: bool) -> Dict[str, Any]:
    return {
        "gameweek": fixture["gameweek"],
        "fixture_fpl_id": fixture["fpl_id"],
        "fixture_understat_id": fixture["understat_id"],
        "kickoff_date": fixture["kickoff_date"],
        "completed": fixture["completed"],
        "team": find_col(fixture, "team", home),
        "opponent": find_col(fixture, "team", not home),
        "home": home,
        "team_xG": find_col(fixture, "xG", home),
        "team_xGA": find_col(fixture, "xG", not home),
        "proj_score": find_col(fixture, "proj_score", home),
        "opponent_proj_score": find_col(fixture, "proj_score", not home),
    }


def get_team_gws(fixtures: Rows) -> Rows:
    rows = []
    for fixture in fixtures:
        rows.append(create_team_gw_row(fixture, True))
        rows.append(create_team_gw_row(fixture, False))
    return rows


def update_fixtures(fixture_ids: Dict[str, Dict[str, int]], fixtures: Rows) -> None:
    for fixture in fixtures:
        home_team = ustat_to_fpl[fixture["h"]["title"]]
        away_team = ustat_to_fpl[fixture["a"]["title"]]
        if home_team not in fixture_ids:
            fixture_ids[home_team] = {}
        fixture_ids[home_team][away_team] = fixture["id"]


async def get_understat_fixtures() -> Dict[str, Dict[str, int]]:
    fixture_ids = {}
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        old_fixtures = await understat.get_league_results("epl", 2021)
        update_fixtures(fixture_ids, old_fixtures)
        upcoming_fixtures = await understat.get_league_fixtures("epl", 2021)
        update_fixtures(fixture_ids, upcoming_fixtures)
    return fixture_ids


def get_match_stats(home_team : str, away_team : str) -> pd.DataFrame:
    try:
        home = fpl_to_fte[home_team]
        away = fpl_to_fte[away_team]
        cols = (df_fte["team1"] == home) & (df_fte["team2"] == away)
        return df_fte[cols].iloc[0]
    except:
        print(
            "Error: fixture {} vs. {} not found in FiveThirtyEight dataset"
            .format(home_team, away_team)
        )
        exit(1)


def get_fixtures() -> List[Dict[str, Any]]:
    fpl_fixtures = requests.get(FPL_FIXTURES_URL).json()
    rows = []
    fixture_id_map = asyncio.run(get_understat_fixtures())
    for fixture in fpl_fixtures:
        home_team = id_to_name[fixture["team_h"]]
        away_team = id_to_name[fixture["team_a"]]
        date = parse_date(fixture["kickoff_time"])
        stats = get_match_stats(home_team, away_team)
        row = {
            "fpl_id": fixture["id"],
            "understat_id": int(fixture_id_map[home_team][away_team]),
            "gameweek": fixture["event"],
            "kickoff_date": date,
            "completed": fixture["finished"],
            "home_team": home_team,
            "away_team": away_team,
            "home_score": stats["score1"],
            "away_score": stats["score2"],
            "home_xG": stats["xg1"],
            "away_xG": stats["xg2"],
            "home_proj_score": stats["proj_score1"],
            "away_proj_score": stats["proj_score2"]
        }
        rows.append(row)
    return rows


def compute_team_xG_averages(db: MySQLManager) -> None:
    """Averages team xG data and writes to the team_gws table.

    Averages are calculated with an exponential moving average (EMA).

    Args:
        db: An instance of MySQLManager to establish a database connection
    """
    teams = get_fpl_teams()
    for team in teams:
        team_name = team["fpl_name"]
        query = """SELECT * FROM team_gws
        WHERE gameweek IS NOT NULL
        ORDER BY kickoff_date"""
        df = db.get_df(query)
        team_rows = df[df["team"] == team_name].reset_index()
        xG = get_ema(team_rows["team_xG"])
        xGA = get_ema(team_rows["team_xGA"])
        for i, r in team_rows.iterrows():
            db.update_row(
                "team_gws",
                {"fixture_fpl_id": r["fixture_fpl_id"], "team": team_name},
                {"avg_team_xG": xG[i], "avg_team_xGA": xGA[i]}
            )


def fixture_id_map() -> Dict[int, int]:
    """Returns a map from understat fixture ids to FPL fixture ids."""
    db = MySQLManager()
    ids = db.exec_query("SELECT understat_id, fpl_id FROM fixtures")
    return dict(ids)


if __name__ == "__main__":
    db = MySQLManager()
    fixtures = get_fixtures()
    db.insert_rows("fixtures", fixtures)
    team_gws = get_team_gws(fixtures)
    db.insert_rows("team_gws", team_gws)
    compute_team_xG_averages(db)
