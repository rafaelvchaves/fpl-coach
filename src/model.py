import numpy as np
import pandas as pd
from constants import *
from scipy.stats import poisson
from db import MySQLManager
from utils import *
from typing import *


def expected(pmf: Callable[[int], float], value: int, max_value: int) -> float:
    """Expected value for a discrete random variable.

    Args:
        pmf: The probability mass function.
        value: The point value of the random variable (for example, the
          goal value for a midfielder is 5).
        max_value: The maximum possible value that the random variable can
        take.

    Returns:
        The expected value of the random variable.
    """
    xp = 0
    for x in range(1, max_value + 1):
        xp += value * x * pmf(x)
    return xp


def predict_points(position, apxG, apxA, amins, abonus, atxG, atxGA, aoxG, aoxGA, proj_score, oproj_score):
    position_params = from_json("../data/params.json")[position]
    goal_value = position_params["goal_value"]
    assist_value = position_params["assist_value"]
    clean_sheet_value = position_params["cs_value"]
    tgcv = position_params["concede_value"]
    xp = []
    attack_multiplier = proj_score / atxG
    def goal_pmf(x): return poisson(attack_multiplier * apxG).pmf(x)
    def assist_pmf(x): return poisson(attack_multiplier * apxA).pmf(x)
    def bonus_pmf(x): return poisson(abonus).pmf(x)
    def cs_pmf(x): return poisson(oproj_score).pmf(0)
    def concede_pmf(x): return poisson(atxGA).pmf(2 * x)

    # can cap goals/assists at 4 since probability beyond that should be negligible anyway
    xp.append(expected(goal_pmf, goal_value, 4))
    xp.append(expected(assist_pmf, assist_value, 4))
    xp.append(expected(bonus_pmf, 1, 3))
    xp.append(expected(cs_pmf, clean_sheet_value, 1))
    xp.append(expected(concede_pmf, tgcv, 4))
    xp.append(2)
    mins_multiplier = min(1, round(amins / 60, 1))
    xp.append(mins_multiplier * np.sum(xp))
    return np.round(xp, 3)


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
    stats = ["goal", "assist", "bonus", "cs", "concede", "minutes"]
    true_cols = [stat + "_points" for stat in stats]
    true_cols.append("total_points")
    predicted_cols = [stat + "_xP" for stat in stats]
    predicted_cols.append("xP")
    rows = df.copy()
    rows[predicted_cols] = rows.apply(predict, axis=1, result_type="expand")
    db = MySQLManager()
    for _, r in rows.iterrows():
        db.update_row(
            "player_gws",
            {"player_name": r["player_name"], "fixture_id": r["fixture_id"]},
            {"xP": r["xP"]}
        )
        db.update_row(
            "player_gws_extra",
            {"player_name": r["player_name"], "fixture_id": r["fixture_id"]},
            {col: r[col] for col in predicted_cols + true_cols}
        )
    rows.to_csv("../data/predicted_final.csv", index=False)
