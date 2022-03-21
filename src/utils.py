import json
import requests
from constants import FPL_BASE_URL
from datetime import datetime
from dateutil import parser
from functools import cmp_to_key


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


def compare_by_index(i):
    """Generates a comparison function for two lists.

    Returns:
      A key comparison functon that compares the values at the ith index
      of the two lists. If the second list element is None, that element will
      go after the first list element.
    """
    def compare_rows(row1, row2):
        date1, date2 = row1[i], row2[i]
        if date2 is None:
            return -1
        elif date1 is None:
            return 1
        elif date1 <= date2:
          return -1
        return 1
    return cmp_to_key(compare_rows)
