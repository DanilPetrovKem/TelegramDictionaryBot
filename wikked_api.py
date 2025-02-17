import requests
import json
import os
from Entry import Entry
from dotenv import load_dotenv
from enums import UserData

class WikkedAPI:
    def __init__(self):
        load_dotenv()
        self.base_url = os.getenv("API_BASE_URL")
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

    def fetch_random(self) -> Entry:
        response = requests.get(f"https://{self.base_url}/random", headers=self.headers)
        random_entry_json = json.loads(response.text)
        if "entry" not in random_entry_json or "etymologies" not in random_entry_json:
            return Entry()
        random_entry = Entry.from_json(random_entry_json)
        return random_entry

if __name__ == "__main__":
    wikked_api = WikkedAPI()
    example = wikked_api.fetch("apple")
    print(example)