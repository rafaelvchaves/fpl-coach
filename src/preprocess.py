import mysql.connector
import numpy as np
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
        rows_to_set = val_rows
        rolling_avg = df.loc[rows_to_get, stat].rolling(
            window=window, closed="left", min_periods=1).mean()
        tdf.loc[rows_to_set, avg_name] = rolling_avg
        if fillna:
            tdf.loc[val_rows, avg_name] = tdf.loc[val_rows,
                                                  avg_name].fillna(method="ffill")
    if drop_old:
        tdf.drop(columns=stat, inplace=True)
    return tdf


def get_player_ema(df, player, stat, alpha):
    ema = df[df["player_name"] == player][stat].ewm(
        alpha=alpha, adjust=False).mean()
    ema = ema.to_numpy()
    ema = np.roll(ema, 1)
    ema[0] = None
    ema = np.round(ema, 3)
    return ema


def compute_emas(df, stats, alpha):
  dfc = df.copy()
  for stat in stats:
    avg_stat = "avg_" + stat
    for player in df["player_name"].unique():
      dfc.loc[df["player_name"] == player, avg_stat] = get_player_ema(df, player, stat, alpha)
    return dfc

def preprocess():
    con = create_engine("mysql://root:password@localhost/fplcoachdb")
    query = open("../scripts/merge.sql").read()
    df = pd.read_sql(query, con)
    df = df.sort_values(by="kickoff_date")
    # df = average_stat(df, "npxG")
    # df = average_stat(df, "xA")
    # df = average_stat(df, "bonus")
    df = average_stat(df, "minutes_played", over_all_games=True)
    df = compute_emas(df, ["npxG", "xA", "bonus"], 0.3)
    df = compute_emas(df, ["minutes_played"], 0.7)
    df.to_csv(GW_HISTORY_FILE, index=False)


if __name__ == "__main__":
    preprocess()
