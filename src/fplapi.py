from constants import FPL_BASE_URL
import requests


def get(url):
    return requests.get(url).json()


def get_players():
    return get(FPL_BASE_URL)["elements"]
