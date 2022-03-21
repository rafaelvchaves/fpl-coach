import datetime
import json
import os
import numpy as np
import pandas as pd
from constants import FIXTURES_FILE, GW_HISTORY_FILE, MERGED_DATA_FILE


def merge():
  gdf = pd.read_csv(GW_HISTORY_FILE)
  fdf = pd.read_csv(FIXTURES_FILE)

  # subsample columns
  fdf = fdf[["fixture_id", "home_team", "away_team"]]

  # merge with fixtures
  df = pd.merge(gdf, fdf, on="fixture_id", how="outer").drop(
      columns=["fixture_id"])

  # set team column
  df.loc[df["home"], "team"] = df["home_team"]
  df.loc[~df["home"], "team"] = df["away_team"]

  # set opposition column
  df.loc[df["home"], "opponent"] = df["away_team"]
  df.loc[~df["home"], "opponent"] = df["home_team"]
  df = df.drop(columns=["home_team", "away_team", "home"])
  df.to_csv(MERGED_DATA_FILE, index=False)
  return df


def average_stat(df, stat, by="name", over_all_games=False, fillna=True, drop_old=False, window=4):
    tdf = df.copy()
    avg_name = "a" + stat
    for val in df[by].unique():
        val_rows = df[by] == val
        rows_to_get = val_rows & (over_all_games | (df["minutes"] > 0) | ~df["completed"])
        rows_to_set = val_rows & df["completed"]
        rolling_avg = df.loc[rows_to_get, stat].rolling(window=window, closed="left", min_periods=1).mean()
        tdf.loc[rows_to_set, avg_name] = rolling_avg
        if fillna:
            tdf.loc[val_rows, avg_name] = tdf.loc[val_rows, avg_name].fillna(method="ffill")
    if drop_old:
        tdf.drop(columns=stat, inplace=True)
    return tdf

def get_data():
  df = pd.read_csv(MERGED_DATA_FILE)
  df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
  df["completed"] = df["date"] < datetime.datetime.today()
  df = average_stat(df, "npxG")
  df = average_stat(df, "xA")
  df = average_stat(df, "bonus")
  df = average_stat(df, "minutes", over_all_games=True)
  return df

if __name__ == "__main__":
  merge()