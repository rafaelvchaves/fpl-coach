import mysql.connector
import pandas as pd
from constants import GW_HISTORY_FILE
from sqlalchemy import create_engine

def average_stat(df, stat, by="player_name", over_all_games=False, fillna=True, drop_old=False, window=4):
    tdf = df.copy()
    avg_name = "a" + stat
    for val in df[by].unique():
        val_rows = df[by] == val
        rows_to_get = val_rows & (over_all_games | (
            df["minutes_played"] > 0) | ~df["completed"])
        rows_to_set = val_rows & df["completed"]
        rolling_avg = df.loc[rows_to_get, stat].rolling(
            window=window, closed="left", min_periods=1).mean()
        tdf.loc[rows_to_set, avg_name] = rolling_avg
        if fillna:
            tdf.loc[val_rows, avg_name] = tdf.loc[val_rows,
                                                  avg_name].fillna(method="ffill")
    if drop_old:
        tdf.drop(columns=stat, inplace=True)
    return tdf


def preprocess():
    con = create_engine('mysql://root:password@localhost/fplcoachdb')
    query = """SELECT player_name, gameweek, player_gws.team AS team,
      completed, minutes_played, npxG, xA, bonus, total_points, price,
      team_xG, team_xGA
      FROM
        player_gws INNER JOIN team_gws
        ON player_gws.fixture_id = team_gws.fixture_id
        AND player_gws.team = team_gws.team
      ORDER BY kickoff_date"""
    df = pd.read_sql(query, con)
    df = average_stat(df, "npxG")
    df = average_stat(df, "xA")
    df = average_stat(df, "bonus")
    df = average_stat(df, "minutes_played", over_all_games=True)
    df.to_csv(GW_HISTORY_FILE, index=False)


if __name__ == "__main__":
    preprocess()
