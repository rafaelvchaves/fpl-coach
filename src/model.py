import numpy as np
import pandas as pd
from constants import GW_HISTORY_FILE
from scipy.stats import poisson
from db import MySQLManager
from utils import *


def expected(pmf, value, max_value):
    xp = 0
    for x in range(1, max_value + 1):
        xp += value * x * pmf(x)
    return xp


def predict_points(position, apxG, apxA, amins, abonus, atxG, atxGA, aoxG, aoxGA, proj_score, oproj_score):
    params = from_json("../data/params.json")
    alpha = params[position]["alpha"]
    beta = params[position]["beta"]
    goal_value = params[position]["goal_value"]
    assist_value = params[position]["assist_value"]
    clean_sheet_value = params[position]["clean_sheet_value"]
    tgcv = params[position]["two_goals_conceded_value"]
    xp = 0

    # def goal_pmf(x): return alpha * poisson(apxG).pmf(x) + \
    #     (1 - alpha) * poisson(aoxGA).pmf(x)
    def goal_pmf(x): return poisson(apxG).pmf(x)
    # def assist_pmf(x): return alpha * poisson(apxA).pmf(x) + \
    #     (1 - alpha) * poisson(aoxGA).pmf(x)
    def assist_pmf(x): return poisson(apxA).pmf(x)
    
    def bonus_pmf(x): return poisson(abonus).pmf(x)
    # def cs_pmf(x): return beta * poisson(atxGA).pmf(0) + \
    #     (1 - beta) * poisson(aoxG).pmf(0)
    def cs_pmf(x): return poisson(oproj_score).pmf(0)

    def concede_pmf(x): return poisson(atxGA).pmf(2 * x)
    xp += expected(goal_pmf, goal_value, 4)
    xp += expected(assist_pmf, assist_value, 4)
    xp += expected(bonus_pmf, 1, 3)
    xp += expected(cs_pmf, clean_sheet_value, 1)
    xp += expected(concede_pmf, tgcv, 4)
    xp += int(amins > 0)
    xp += int(amins > 59)
    multiplier = proj_score / atxG
    return np.round(multiplier * xp, 3)


def predict(row):
    return predict_points(
        row["position"],
        row["avg_npxG"],
        row["avg_xA"],
        row["avg_minutes"],
        row["avg_bonus"],
        row["avg_team_xG"],
        row["avg_team_xGA"],
        row["avg_opponent_xG"],
        row["avg_opponent_xGA"],
        row["proj_score"],
        row["opponent_proj_score"]
    )

# TODO: add function that evaluates model and prints metrics when this script
# is run

# will need to do hyperparameter tuning for each EMA alpha, probably collecting
# more data to break up point total into points from goals, clean sheets, etc.


if __name__ == "__main__":
    df = pd.read_csv(GW_HISTORY_FILE)
    # rows = df[~df["completed"]].copy()
    rows = df.copy()
    rows["xP"] = rows.apply(predict, axis=1)
    db = MySQLManager()
    for _, r in rows.iterrows():
        db.update_row(
            "player_gws",
            {"player_name": r["player_name"], "fixture_id": r["fixture_id"]},
            {"xP": r["xP"]}
        )
