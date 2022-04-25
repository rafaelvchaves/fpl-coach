"""A module for preprocessing gameweek data to be fed into model."""
from constants import (
    GW_HISTORY_FILE,
    MERGE_SCRIPT,
    NPXG_ALPHA,
    XA_ALPHA,
    BONUS_ALPHA,
    MINUTES_ALPHA
)
from db import MySQLManager
from teams import get_fpl_teams
from utils import get_ema


def compute_emas(data, stats, alpha):
    """Computes an EMA for each of the specified stats."""
    dfc = data.copy()
    for stat in stats:
        avg_stat = f"avg_{stat}"
        for player in data["player_name"].unique():
            is_player = data["player_name"] == player
            row = data[is_player]
            dfc.loc[is_player, avg_stat] = get_ema(row[stat], alpha)
    return dfc


def compute_team_xg_averages(db: MySQLManager) -> None:
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
        team_xg = get_ema(team_rows["team_xG"], NPXG_ALPHA)
        team_xga = get_ema(team_rows["team_xGA"])
        for i, team_row in team_rows.iterrows():
            db.update_row(
                "team_gws",
                {"fixture_id": team_row["fixture_id"], "team": team_name},
                {"avg_team_xG": team_xg[i], "avg_team_xGA": team_xga[i]}
            )


def preprocess():
    """Preprocess data and write to gameweek history file.

    Joins the player_gws table with team_gws table and computes stat averages."""
    db = MySQLManager()
    compute_team_xg_averages(db)
    with open(MERGE_SCRIPT, encoding="utf-8") as sql_file:
        query = sql_file.read()
    gw_df = db.get_df(query)
    gw_df = compute_emas(gw_df, ["npxG"], NPXG_ALPHA)
    gw_df = compute_emas(gw_df, ["xA"], XA_ALPHA)
    gw_df = compute_emas(gw_df, ["bonus"], BONUS_ALPHA)
    gw_df = compute_emas(gw_df, ["minutes"], MINUTES_ALPHA)
    gw_df.to_csv(GW_HISTORY_FILE, index=False)


if __name__ == "__main__":
    preprocess()
