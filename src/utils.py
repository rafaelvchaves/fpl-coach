import json
import requests
from constants import FPL_BASE_URL
from datetime import datetime
from dateutil import parser

def parse_date(s):
    """Converts a string to a string in the form YYYY-MM-DD.

    Returns:
      None if s is None, otherwise a string in the form YYYY-MM-DD.""
    """
    if s is None:
        return None
    return parser.parse(s).strftime("%Y-%m-%d")


def from_json(path):
    """Returns a dictionary loaded from the json file given by path."""
    with open(path) as f:
        return json.load(f)

def to_json(path, j):
    with open(path, "w") as f:
        json.dump(j, f, indent=4, ensure_ascii=False)


def get_current_gw():
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
