import requests

QUOTES_API_URL = "https://api.quotable.io/random"

def get_quote():
    response = requests.get(QUOTES_API_URL)
    data = response.json()
    return data["content"] + " - " + data["author"]
