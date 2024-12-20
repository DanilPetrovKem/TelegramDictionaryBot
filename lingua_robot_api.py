import os
import logging
import requests
import json

class LinguaRobotAPIClient:
    def __init__(self):
        self.host = "lingua-robot.p.rapidapi.com"
        self.key = os.getenv("WORDSAPI_KEY")
        self.base_url = f"https://{self.host}/language/v1/entries/en"
        self.test_folder = "test_data"
        self.debug = os.getenv("DEBUG") == "True"

    def fetch_data(self, word: str) -> dict:
        if self.debug:
            try: return self.fetch_test_data(word)
            except FileNotFoundError:
                pass
        url = f"{self.base_url}/{word}"
        headers = {
            "X-RapidAPI-Host": self.host,
            "X-RapidAPI-Key": self.key,
        }
        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data for word '{word}': {e}")
            return None
        
    def fetch_test_data(self, word: str) -> dict:
        with open(f"{self.test_folder}/{word}.json", "r", encoding="utf-8") as file:
            return json.load(file)