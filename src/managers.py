import os
import requests

session = requests.session()

url = "https://users.premierleague.com/accounts/login/"
payload = {
    "password": os.environ["FPL_PASSWORD"],
    "login": os.environ["FPL_USERNAME"],
    "redirect_uri": "https://fantasy.premierleague.com/a/login/",
    "app": "plfpl-web"
}
print(session.post(url, data=payload))
# response = session.get('https://fantasy.premierleague.com/api/my-team/505657/')
