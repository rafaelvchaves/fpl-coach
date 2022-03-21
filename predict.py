import numpy as np
from preprocess import get_data
from scipy.stats import poisson
from utils import from_json
from functools import partial


def expected(pmf, value, max_value):
    xp = 0
    for x in range(1, max_value + 1):
        xp += value * x * pmf(x)
    return xp

def predict_points(alpha, beta, position, apxG, apxA, amins, abonus, atxG, atxGA, aoxG, aoxGA):
    params = from_json("data/params.json")
    # alpha = params[position]["alpha"]
    # beta = params[position]["beta"]
    goal_value = params[position]["goal_value"]
    assist_value = params[position]["assist_value"]
    clean_sheet_value = params[position]["clean_sheet_value"]
    tgcv = params[position]["two_goals_conceded_value"]
    xp = 0

    def goal_pmf(x): return alpha * poisson(apxG).pmf(x) + \
        (1 - alpha) * poisson(aoxGA).pmf(x)
    def assist_pmf(x): return alpha * poisson(apxA).pmf(x) + \
        (1 - alpha) * poisson(aoxGA).pmf(x)

    def bonus_pmf(x): return poisson(abonus).pmf(x)
    def cs_pmf(x): return beta * poisson(atxGA).pmf(0) + \
        (1 - beta) * poisson(aoxG).pmf(0)

    def concede_pmf(x): return poisson(atxGA).pmf(2 * x)
    # print("clean sheet probability with beta = {}: {}".format(beta, cs_pmf(0)))
    xp += expected(goal_pmf, goal_value, 4)
    xp += expected(assist_pmf, assist_value, 4)
    xp += expected(bonus_pmf, 1, 3)
    xp += expected(cs_pmf, clean_sheet_value, 1)
    xp += expected(concede_pmf, tgcv, 4)
    xp += int(amins > 0)
    xp += int(amins > 59)
    return xp

alpha = 1
beta = 1

def predict(alpha, beta, row):
    return predict_points(
        alpha,
        beta,
        row["position"],
        row["apxG"],
        row["apxA"],
        row["amins"],
        row["apbonus"],
        row["atxG"],
        row["atxGA"],
        row["aoxG"],
        row["aoxGA"]
    )

if __name__ == "__main__":
  df = get_data()
  sample = df[(df["minutes"] > 0) & (df["position"] == "M")].sample(n=1000).copy()
  # print(sample["name"].iloc[0], sample["opponent"].iloc[0])
  # print("average xG conceded: {}, opponent average xG: {}".format(
  #   sample["atxGA"].iloc[0], sample["aoxG"].iloc[0]
  # ))

  # alpha = 1
  beta = 0.3
  min_alpha = 0
  min_err = np.inf
  for alpha in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
    predict_ab = partial(predict, alpha, beta)
    sample.loc[:, "xP"] = sample.apply(predict_ab, axis=1)
    sample.loc[:, "error"] = np.abs(sample["xP"] - sample["points"])
    err = sample["error"].mean()
    if err < min_err:
      min_err = err
      min_alpha = alpha
  print(min_alpha, min_err)
  # print(sample.sort_values(ascending=False, by='error'))