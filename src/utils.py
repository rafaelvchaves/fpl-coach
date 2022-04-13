import json
import numpy as np
import pandas as pd
import requests
from constants import FPL_BASE_URL
from datetime import datetime
from dateutil import parser
from typing import Optional


def cast_float_safe(s: Optional[str]) -> Optional[float]:
    if s is None:
        return None
    return round(float(s), 3)


def cast_int_safe(s: Optional[str]) -> Optional[int]:
    return None if s is None else int(s)


def parse_date(s: Optional[str]) -> Optional[str]:
    """Converts a string to a string in the form YYYY-MM-DD.

    Returns:
      None if s is None, otherwise a string in the form YYYY-MM-DD.""
    """
    if s is None:
        return None
    return parser.parse(s).strftime("%Y-%m-%d")


def from_json(path: str) -> dict:
    """Returns a dictionary loaded from the json file given by path."""
    with open(path) as f:
        return json.load(f)


def to_json(path: str, j: dict) -> None:
    """Writes dictionary to specified json file."""
    with open(path, "w") as f:
        json.dump(j, f, indent=4, ensure_ascii=False)


def get_current_gw() -> int:
    """Gets the current FPL gameweek.

    The current gameweek is defined as the gameweek whose deadline was most
    recently passed.

    Returns:
      -1 if no such gameweek exists
    """
    gws = requests.get(FPL_BASE_URL).json()["events"]
    now = datetime.utcnow()
    for gw in gws:
        gw_deadline = datetime.strptime(
            gw['deadline_time'], '%Y-%m-%dT%H:%M:%SZ')
        if gw_deadline > now:
            return gw["id"] - 1
    return -1


def get_ema(col: pd.Series, alpha: float = 0.3) -> np.array:
    """Computes a simple exponential moving average of a pandas Series.

    Args:
        col: A pandas Series to compute the average over.
        alpha: The ema parameter.

    Returns:
        A numpy array with the EMA of col. The EMA is shifted by one, i.e. it
        only depends on "old" data. If either the old average or the new data
        point are nan, it will simply copy over the non-nan value, if any.
        More concretely,
        ema[0] = nan
        ema[i] = {
            nan if col[i-1] = nan and ema[i-1] = nan
            col[i-1] if col[i-1] <> nan, ema[i-1] = nan
            y[i-1] if col[i-1] = nan, ema[i-1] <> nan
            alpha * col[i-1] + (1 - alpha) * ema[i-1] otherwise
        }
        Typically, col will be a vector of match stats ordered by time, and so
        before gameweek i, we only know the match stats and the average from
        gameweek i-1. 
    """
    ema = col.ewm(alpha=alpha, ignore_na=True, adjust=False).mean()
    ema = ema.to_numpy()
    ema = np.roll(ema, 1)
    ema[0] = np.nan
    ema = np.round(ema, 3)
    return ema