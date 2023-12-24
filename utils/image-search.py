import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Replace with your actual credentials
API_KEY = os.getenv("API_KEY")
CX = os.getenv("CX")

def image_search(query):
    url = f"https://customsearch.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CX,
        "q": query,
        "searchType": "image"
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data["items"]:
        return data["items"][0]["link"]  # Return the first image link
    else:
        return "No images found."
