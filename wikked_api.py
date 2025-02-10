import requests
import json
import os
from Entry import Entry, Etymology, Lexeme, Sense
from dotenv import load_dotenv

class WikkedAPI:
    def __init__(self):
        load_dotenv()
        self.base_url = "wikked1.p.rapidapi.com"
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY")
        self.headers = {
            "x-rapidapi-key": self.rapidapi_key,
            "x-rapidapi-host": self.base_url
        }
        self.fetch_url = f"https://{self.base_url}/entries/"
    
    def fetch(self, requested_entry: str) -> Entry:
        response = requests.get(self.fetch_url + requested_entry, headers=self.headers)
        entry_json = json.loads(response.text)
        if "entry" not in entry_json or "etymologies" not in entry_json:
            return Entry()
        entry = Entry.from_json(entry_json)
        return entry


if __name__ == "__main__":
    wikked_api = WikkedAPI()
    example = wikked_api.fetch("apple")
    print(example)