import unidecode
import fbrefscraper
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import json
import utils
import random
import time
import urllib


def get_id(player):
    path = "../data/json/fpl_fbref_ids.json"
    ids = {}
    if os.path.exists(path):
        ids = utils.from_json(path)
        if player["id"] in ids:
            return ids[player["id"]]
    fbref_id = fbrefscraper.get_id(player)
    ids[player["id"]] = fbref_id
    utils.to_json(path, ids)
    return fbref_id


def exponential_backoff(f, max_retries=5, backoff=1):
    retries = 0
    while True:
        try:
            return f()
        except urllib.error.HTTPError:
            if retries == max_retries:
                print("Max retries reached")
                raise
            else:
                time.sleep(backoff * 2 ** retries + random.uniform(0, 1))
                retries += 1


def clean(x):
  try:
    return float(x)
  except:
    return 0.0

# def get_season_stats_KEEP(player_id, season):
#     url = f"https://fbref.com/en/players/{player_id}/matchlogs/{season}/"
#     df = exponential_backoff(lambda: pd.read_html(url)[0])
#     try:
#         print(df["Expected"]["npxG"].apply(clean))
#         print(df["Expected"]["xA"].apply(clean))
#     except KeyError:
#         print(url)


def get_season_stats(player_id, season):
    url = f"https://fbref.com/en/players/{player_id}/dom_lg/"
    try:
      df = exponential_backoff(lambda: pd.read_html(url)[0])
      stats = df[df["Unnamed: 0_level_0"]["Season"] == season]["Per 90 Minutes"].iloc[0]
      print(stats["npxG"])
      print(stats["xA"])
      return {
        "npxG": stats["npxG"],
        "xA": stats["xA"]
      }
    except Exception as e:
        print(e)
        print(url)
        return {
        "npxG": 0.0,
        "xA": 0.0
      }