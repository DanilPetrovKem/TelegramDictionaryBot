import os
import logging
import requests

class WordsAPIClient:
    def __init__(self):
        self.host = os.getenv("WORDSAPI_HOST")
        self.key = os.getenv("WORDSAPI_KEY")
        self.base_url = f"https://{self.host}/words"

    def fetch_word_data(self, word: str) -> dict:
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