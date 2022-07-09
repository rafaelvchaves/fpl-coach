import urllib.request
from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import os
import time
import unidecode
from difflib import SequenceMatcher

HTML_CACHE_DIR = "../data/html"


def clean(name):
    return unidecode.unidecode(name).lower().replace("-", " ")


def matches(name, names):
    for candidate_name in names:
        if clean(name) == clean(candidate_name):
            return True
    return False


def check_cache(name):
    cache_file = os.path.join(HTML_CACHE_DIR, f"{name}.html")
    if not os.path.exists(cache_file):
        return None, False
    with open(cache_file, "rb") as f:
        return f.read(), True


def write_cache(name, html):
    cache_file = os.path.join(HTML_CACHE_DIR, f"{name}.html")
    with open(cache_file, "wb") as f:
        f.write(html)


def fetch(url, cache_file, cache):
    if cache:
        html, ok = check_cache(cache_file)
        if ok:
            return html, True
    response = requests.get(url)
    if response.status_code == 429:
        print(f"Too many requests sent to {url}")
        return None, False
    html = response.content
    write_cache(cache_file, html)
    return html, True


def candidate_names(player):
    return [
        player["web_name"],
        player["first_name"] + " " + player["second_name"],
        player["first_name"] + " " + player["web_name"]
    ]


def extract_id(p):
    try:
        return p.find("a")["href"].split("/")[3]
    except:
        return None


def string(player):
    return f"{player['web_name']} ({player['id']})"


def search(prefix, player):
    html, ok = fetch(
        f"https://fbref.com/en/players/{prefix}/", prefix, cache=True)
    if not ok:
        return None
    bs = BeautifulSoup(html, 'html.parser')
    for p in bs.find_all("p"):
        name = p.find("strong")
        if name == None:
            continue
        names = candidate_names(player)
        if matches(name.text, names):
            fbref_id = extract_id(p)
            if fbref_id is not None:
                return fbref_id
    return None


def get_prefix(s):
    return unidecode.unidecode(s[:2].lower())


def get_id_from_index(player):
    prefixes = [
        get_prefix(player['web_name'].split(" ")[-1]),
        get_prefix(player['second_name']),
        get_prefix(player['second_name'].split(" ")[-1])
    ]
    for prefix in prefixes:
        fbref_id = search(prefix, player)
        if fbref_id is not None:
            return fbref_id
    print(f"not found: {string(player)}")
    return None


team_ids = {
    1: "18bb7c10",
    2: "8602292d",
    3: "4ba7cbea",
    4: "cd051869",
    5: "d07537b9",
    6: "cff3d9bb",
    7: "47c64c55",
    8: "d3fd31cc",
    9: "fd962109",
    10: "a2d435b3",
    11: "5bfb9659",
    12: "822bd0ba",
    13: "b8fd03ef",
    14: "19538871",
    15: "b2b47a98",
    16: "e4a775cb",
    17: "33c895d4",
    18: "361ca564",
    19: "7c21e445",
    20: "8cec06e1"
}


def get_players(team_id, season):
    squad = {}
    team_fbref_id = team_ids[team_id]
    url = f"https://fbref.com/en/squads/{team_fbref_id}/{season}/"
    html, ok = fetch(url, f"squad-{team_id}-{season}", True)
    if not ok:
        exit(1)
    bs = BeautifulSoup(html, 'html.parser')
    table = bs.find("tbody").find_all("th")
    for row in table:
        try:
            fbref_id, name = row["data-append-csv"], row.find("a").text
            squad[fbref_id] = name
        except:
            continue
    return squad


hardcoded_conversions = {
    7: "79300479",
    10: "35e413f1",
    42: "66b76d44",
    505: "10a10454",
    79: "df0a4c90",
    125: "9cfbad36",
    172: "45685411",
    194: "30d4a2e5",
    205: "0f7533cd",
    243: "d102b8a2",
    286: "7a11550b",
    292: "f315ca93",
    297: "4d77b365",
    500: "7bf9400b",
    320: "387e1d35",
    346: "6639e500",
    395: "10ec4169",
    415: "5e105217",
    419: "afed6722",
    433: "8b04d6c1",
    445: "df8b52a5",
    450: "feb5d972",
    477: "e28868f3",
    491: "9a28eba4"
}


def get_id(player):
    if player["id"] in hardcoded_conversions:
        return hardcoded_conversions[player["id"]]
    squad_players = get_players(player["team"], "2021-2022")
    names = candidate_names(player)
    for fbref_id, name in squad_players.items():
        if matches(name, names):
            return fbref_id
    return get_id_from_index(player)


def get_match_stats(player_id, fixture_id):
    pass
