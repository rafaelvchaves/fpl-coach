import unidecode
import fbrefscraper
import pandas as pd
import requests
from bs4 import BeautifulSoup


def get_id(player):
    return fbrefscraper.get_id(player)


def get_season_stats(player_id, season):
    # df = pd.read_html("https://fbref.com/en/players/79300479/matchlogs/s11160/summary")[0]
    # print(df["Expected"])
    pass

