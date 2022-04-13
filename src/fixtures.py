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

Row = Dict[str, Any]
Rows = List[Row]


def get_fte_df() -> pd.DataFrame:
    """Returns data from FiveThirtyEight's SPI csv as a pandas DataFrame."""
    df = pd.read_csv(FTE_MATCHES_URL)
    df = df[(df["league"] == "Barclays Premier League")
            & (df["season"] == 2021)]
    cols = ["date", "team1", "team2", "proj_score1",
            "proj_score2", "score1", "score2", "xg1", "xg2"]
    return df[cols]


df_fte = get_fte_df()


def find_col(fixture: Row, col: str, home: bool) -> Any:
    return fixture["home_" + col if home else "away_" + col]


def create_team_gw_row(fixture: Row, home: bool) -> Row:
    """Prepares a row for the team_gws table, from a row from the fixtures table."""
    return {
        "gameweek": fixture["gameweek"],
        "fixture_id": fixture["fpl_id"],
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
    """Gets rows for the team_gws table from rows from the fixtures table.

    Args:
        fixtures: A list of dictionaries mapping a column name from the fixtures
          table to its value for that row.

    Returns:
        A list of rows to be inserted into the team_gws table.
    """
    rows = []
    for fixture in fixtures:
        rows.append(create_team_gw_row(fixture, True))
        rows.append(create_team_gw_row(fixture, False))
    return rows


def update_fixtures(fixture_ids: Dict[str, Dict[str, int]], fixtures: Rows) -> None:
    """Updates the fixture_ids map with a list of fixtures.

    Args:
        fixture_ids: A dictionary mapping a home team and an away team to
          their understat ID.
        fixtures: The list of fixtures to be added to fixture_ids.
    """
    for fixture in fixtures:
        home_team = ustat_to_fpl[fixture["h"]["title"]]
        away_team = ustat_to_fpl[fixture["a"]["title"]]
        if home_team not in fixture_ids:
            fixture_ids[home_team] = {}
        fixture_ids[home_team][away_team] = fixture["id"]


async def get_understat_fixtures() -> Dict[str, Dict[str, int]]:
    """Returns a dictionary of fixture ids from understat.

    Used for matching up FPL fixtures with understat fixtures."""
    fixture_ids = {}
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        old_fixtures = await understat.get_league_results("epl", 2021)
        update_fixtures(fixture_ids, old_fixtures)
        upcoming_fixtures = await understat.get_league_fixtures("epl", 2021)
        update_fixtures(fixture_ids, upcoming_fixtures)
    return fixture_ids


def get_match_stats(home_team: str, away_team: str) -> pd.DataFrame:
    """Returns a single row of a pandas DataFrame with match stats.

    Requires:
        The fixture must be from the current Premier League season.
    """
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


def get_fixtures() -> Rows:
    """Returns all of the rows to be inserted into the fixtures table."""
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

    Averages are calculated with an exponential moving average (EMA)."""
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
                {"fixture_id": r["fixture_id"], "team": team_name},
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
