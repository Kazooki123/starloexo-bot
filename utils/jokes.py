import requests

JOKES_API_URL = "https://api.chucknorris.io/jokes/random"

def get_joke():
    response = requests.get(JOKES_API_URL)
    data = response.json()
    return data["value"]
