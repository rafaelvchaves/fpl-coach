"""A module for utility functions."""
import json
import math
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import pandas as pd
import requests
from dateutil import parser
import numpy as np
from constants import FPL_BASE_URL

# type synonyms for database rows
Row = Dict[str, Any]
Rows = List[Row]


def cast_float_safe(str_opt: Optional[str]) -> Optional[float]:
    """Cast optional string to float, returning None if str_opt is None."""
    if str_opt is None:
        return None
    return round(float(str_opt), 3)


def cast_int_safe(str_opt: Optional[str]) -> Optional[int]:
    """Cast optional string to int, returning None if str_opt is None."""
    return None if str_opt is None else int(str_opt)


def parse_date(str_opt: Optional[str]) -> Optional[str]:
    """Converts a string to a string in the form YYYY-MM-DD.

    Returns:
      None if s is None, otherwise a string in the form YYYY-MM-DD.""
    """
    if str_opt is None:
        return None
    return parser.parse(str_opt).strftime("%Y-%m-%d")


def from_json(path: str) -> dict:
    """Returns a dictionary loaded from the json file given by path."""
    with open(path, encoding="utf-8") as json_file:
        return json.load(json_file)


def to_json(path: str, json_dict: dict) -> None:
    """Writes dictionary to specified json file."""
    with open(path, "w", encoding="utf-8") as json_file:
        json.dump(json_dict, json_file, indent=4, ensure_ascii=False)


def get_current_gw() -> int:
    """Gets the current FPL gameweek.

    The current gameweek is defined as the gameweek whose deadline was most
    recently passed.

    Returns:
      39 if no such gameweek exists
    """
    gws = requests.get(FPL_BASE_URL).json()["events"]
    now = datetime.utcnow()
    for gw in gws:
        gw_deadline = datetime.strptime(
            gw['deadline_time'], '%Y-%m-%dT%H:%M:%SZ')
        if gw_deadline > now:
            return gw["id"] - 1
    return 39


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


def mapl(f: Callable[[Any], Any], lst: List[Any]) -> List[Any]:
    """Map helper function to avoid wrapping in list() call each time."""
    return list(map(f, lst))


def get_gw_range(gws: Optional[Union[int, Tuple[int]]]) -> Tuple[int]:
    """Helper function for parsing a gameweek argument into a range. """
    current_gw = get_current_gw()
    if isinstance(gws, int):
        return gws, gws
    if isinstance(gws, tuple):
        return gws[0], min(gws[1], current_gw)
    return 1, min(current_gw, 38)


def subset_dict(d: Dict[Any, Any], keys: List[Any]) -> Dict[Any, Any]:
    """Returns a copy of a dictionary with only the specified keys."""
    return {k: d[k] for k in keys}


def isnan(val: Any) -> bool:
    """Checks if any value is nan."""
    try:
        return math.isnan(float(val))
    except ValueError:
        return False


def prepare_string(val: Any) -> str:
    """Converts a value into a string to be used in a SQL query.

    Args:
        val: The value to convert to a string.

    Returns:
        A string conversion of the value. For None values, the string "NULL" is
        retruned. Strings are wrapped in single quotes, and apostrophes are
        also escaped. For example,
        prepare_string("N'Golo Kante") yields "'N''Golo Kante'".
    """
    if val is None or isnan(val):
        return "NULL"
    if isinstance(val, str):
        val_escaped = val.replace("'", "''")
        return f"'{val_escaped}'"
    return str(val)
