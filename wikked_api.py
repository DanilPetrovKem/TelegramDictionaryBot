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
        entry = Entry()
        entry.redirected = entry_json["redirected"]
        entry.entry = entry_json["entry"]
        for etymology_json in entry_json["etymologies"]:
            etymology = Etymology()
            for lexeme_json in etymology_json["lexemes"]:
                lexeme = Lexeme()
                lexeme.lemma = lexeme_json["lemma"]
                lexeme.part_of_speech = lexeme_json["part_of_speech"]
                for sense_json in lexeme_json["senses"]:
                    sense = Sense()
                    sense.definition = sense_json["definition"]
                    sense.labels = sense_json["labels"]
                    sense.examples = sense_json["examples"]
                    sense.synonyms = sense_json["synonyms"]
                    sense.antonyms = sense_json["antonyms"]
                    sense.collocations = sense_json["collocations"]
                    lexeme.senses.append(sense)
                etymology.lexemes.append(lexeme)
            entry.etymologies.append(etymology)
        return entry
        


if __name__ == "__main__":
    wikked_api = WikkedAPI()
    free = wikked_api.fetch("free")
    print(free)
