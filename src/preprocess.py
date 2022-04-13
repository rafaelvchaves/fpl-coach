import numpy as np
from constants import GW_HISTORY_FILE
from db import MySQLManager
from utils import *


def compute_emas(df, stats, alpha):
    dfc = df.copy()
    for stat in stats:
        avg_stat = "avg_" + stat
        for player in df["player_name"].unique():
            row = df[df["player_name"] == player]
            dfc.loc[df["player_name"] == player,
                    avg_stat] = get_ema(row[stat], alpha)
    return dfc


def preprocess():
    db = MySQLManager()
    query = open("../scripts/merge.sql").read()
    df = db.get_df(query)
    df = df.sort_values(by="kickoff_date")
    df = compute_emas(df, ["npxG", "xA", "bonus"], 0.3)
    df = compute_emas(df, ["minutes"], 0.7)
    df.to_csv(GW_HISTORY_FILE, index=False)


if __name__ == "__main__":
    preprocess()
