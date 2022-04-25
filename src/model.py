"""A statistics-based model for predicting FPL points."""
from typing import Callable
import numpy as np
import pandas as pd
from scipy.stats import poisson
from constants import (
    GW_HISTORY_FILE,
    RUNS_FILE,
    NPXG_ALPHA,
    XA_ALPHA,
    BONUS_ALPHA,
    MINUTES_ALPHA
)
from db import MySQLManager
from preprocess import preprocess
from utils import from_json, to_json, get_current_gw

params_json = from_json("../data/params.json")
predicted_cols = [
    "goal_xP", "assist_xP", "cs_xP", "bonus_xP", "concede_xP", "xP"
]

point_cols = [
    "goal_points", "assist_points", "cs_points", "bonus", "concede_points"
]

stat_cols = [
    "goals_scored", "assists", "clean_sheets", "bonus", "goals_conceded"
]


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
        xp += x * pmf(x)
    return value * xp


def predict(row: pd.Series) -> np.ndarray:
    """Make predictions on a single gameweek.

    Args:
        row: A pandas series containing player data from a single gameweek.

    Returns:
        A numpy array with the following values, in order:
          [goal_xP, assist_xP, clean_sheet_xP, bonus_xP, goals_conceded_xP, xP].
          Note that xP is not necessarily the sum of the other xPs, as there
          is a multiplier based on how many minutes a player has recently
          played.
    """
    xp = []
    stat_values = params_json[row["position"]]["stat_values"]
    attack_multiplier = row["proj_score"] / row["avg_team_xG"]

    def goal_pmf(x):
        return poisson(attack_multiplier * row["avg_npxG"]).pmf(x)

    def assist_pmf(x):
        return poisson(attack_multiplier * row["avg_xA"]).pmf(x)

    def bonus_pmf(x):
        return poisson(row["avg_bonus"]).pmf(x)

    def cs_pmf(_):
        return poisson(row["opponent_proj_score"]).pmf(0)

    def concede_pmf(x):
        return poisson(row["opponent_proj_score"]).pmf(2 * x)

    # can cap goals/assists at 4 since probability beyond that should be negligible anyway
    xp.append(expected(goal_pmf, stat_values[0], 4))
    xp.append(expected(assist_pmf, stat_values[1], 4))
    xp.append(expected(cs_pmf, stat_values[2], 1))
    xp.append(expected(bonus_pmf, stat_values[3], 3))
    xp.append(expected(concede_pmf, stat_values[4], 4))
    mins_multiplier = min(1, round(row["avg_minutes"] / 60, 1))
    # Add 2 for base minute points
    xp.append(mins_multiplier * (np.sum(xp) + 2))
    return np.round(xp, 3)


def calculate_points(row: pd.Series) -> pd.Series:
    """Returns inner product of the stat columns and their point values."""
    point_values = params_json[row["position"]]["stat_values"]
    return row[stat_cols] * point_values


def evaluate(rows: pd.Series) -> None:
    """Calculates evaluation metrics for a single gameweek row."""
    known_point_totals = rows[rows["gameweek"] < get_current_gw()].copy()
    known_point_totals[point_cols] = known_point_totals.apply(
        calculate_points, axis=1, result_type="expand")
    all_point_cols = point_cols + ["total_points"]
    known_point_totals["concede_points"] = - \
        known_point_totals["goals_conceded"] // 2
    actual_points = known_point_totals[all_point_cols].to_numpy()
    predicted_points = known_point_totals[predicted_cols].to_numpy()
    diff_sq = np.power(actual_points - predicted_points, 2)
    rmse = np.round(np.sqrt(np.sum(diff_sq, axis=0)), 1)
    print("RMSE: ", rmse)
    runs = from_json(RUNS_FILE)
    runs.append({
        "npxG_alpha": NPXG_ALPHA,
        "xA_alpha": XA_ALPHA,
        "bonus_alpha": BONUS_ALPHA,
        "minutes_alpha": MINUTES_ALPHA,
        "rmse": rmse.tolist()
    })
    to_json(RUNS_FILE, runs)


if __name__ == "__main__":
    preprocess()
    df = pd.read_csv(GW_HISTORY_FILE)
    gws = df[df["avg_minutes"] > 0].copy()
    gws[predicted_cols] = gws.apply(
        predict, axis=1, result_type="expand")
    gws_zero_mins = df[df["avg_minutes"] == 0].copy()
    gws_zero_mins[predicted_cols] = 0
    # gws.to_csv("../data/predictions.csv", index=False)
    evaluate(gws)
    all_gw_data = pd.concat([gws, gws_zero_mins])
    db = MySQLManager()
    for _, entry in all_gw_data.iterrows():
        db.update_row(
            "player_gws_predicted",
            {
                "player_id": entry["player_id"],
                "fixture_id": entry["fixture_id"]
            },
            {col: entry[col] for col in predicted_cols}
        )
