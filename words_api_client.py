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
        
    def fetch_random_word(self) -> str:
        url = self.base_url
        querystring = {"random":"true"} 
        headers = {
            "X-RapidAPI-Host": self.host,
            "X-RapidAPI-Key": self.key,
        }
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=5)
            response.raise_for_status()
            return response.json().get("word", "")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching random word: {e}")
            return ""
        
    def fetch_rhymes(self, word: str) -> list:
        url = f"{self.base_url}/{word}/rhymes"
        headers = {
            "X-RapidAPI-Host": self.host,
            "X-RapidAPI-Key": self.key,
        }
        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            rhymes = response.json().get("rhymes", {}).get("all", [])
            # Filter our all rhymes which contain the word itself
            filtered_rhymes = [rhyme for rhyme in rhymes if word not in rhyme]
            # Filter out all rhymes which contain spaces
            filtered_rhymes = [rhyme for rhyme in filtered_rhymes if " " not in rhyme]
            print(f"Filtered rhymes: {filtered_rhymes}")
            return filtered_rhymes
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching rhymes for word '{word}': {e}")
            return []

    def get_definition_list(self, data: dict) -> list:
        results = data.get("results", [])
        if not results:
            return []
        return [r.get("definition", "No definition available.") for r in results]
    
    def get_synonym_list(self, data: dict) -> list:
        results = data.get("results", [])
        all_synonyms = {synonym for r in results for synonym in r.get("synonyms", [])}
        return sorted(all_synonyms)
    
    def get_antonym_list(self, data: dict) -> list:
        results = data.get("results", [])
        all_antonyms = {antonym for r in results for antonym in r.get("antonyms", [])}
        return sorted(all_antonyms)
    