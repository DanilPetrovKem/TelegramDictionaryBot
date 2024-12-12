import json
import os
import logging
from localization_keys import Phrases
from typing import Any, List, Optional

class LocalizationError(Exception):
    pass

class Localization:
    # Add a static property locales
    locales = []

    def __init__(self, locale: str = "en"):
        self.locale = locale
        self.strings = {}
        self.load_locale()

    def load_locale(self):
        locale_path = os.path.join(os.path.dirname(__file__), "locales", f"{self.locale}.json")
        try:
            with open(locale_path, "r", encoding="utf-8") as file:
                self.strings = json.load(file)
        except FileNotFoundError:
            logging.warning(f"Localization file for '{self.locale}' not found. Falling back to 'en'.")
            fallback_path = os.path.join(os.path.dirname(__file__), "locales", "en.json")
            try:
                with open(fallback_path, "r", encoding="utf-8") as fallback_file:
                    self.strings = json.load(fallback_file)
            except FileNotFoundError:
                raise LocalizationError("Fallback localization file 'en.json' not found.")

    def get(self, key: Phrases, **kwargs: Any) -> str:
        message = self.strings.get(key.name)
        if message is None:
            raise LocalizationError(f"Missing localization key: '{key.name}'")

        if kwargs:
            try:
                message = message.format(**kwargs)
            except KeyError as e:
                raise LocalizationError(f"Missing placeholder for key '{key.name}': {e}") from e
        return message

    @classmethod
    def validate_localizations(cls) -> None:
        locales_dir = os.path.join(os.path.dirname(__file__), "locales")
        locales = [
            filename.split(".")[0] for filename in os.listdir(locales_dir)
            if filename.endswith(".json")
        ]
            
        enum_keys = {phrase.name for phrase in Phrases}
        all_valid = True

        for locale in locales:
            locale_path = os.path.join(os.path.dirname(__file__), "locales", f"{locale}.json")
            try:
                with open(locale_path, "r", encoding="utf-8") as file:
                    strings = json.load(file)
                file_keys = set(strings.keys())

                missing_keys = enum_keys - file_keys
                extra_keys = file_keys - enum_keys

                if missing_keys:
                    logging.error(f"[{locale}] Missing keys: {missing_keys}")
                    all_valid = False
                if extra_keys:
                    logging.warning(f"[{locale}] Extra keys not in Phrases enum: {extra_keys}")
            except FileNotFoundError:
                logging.error(f"Localization file for '{locale}' not found.")
                all_valid = False
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in '{locale}.json': {e}")
                all_valid = False

        if not all_valid:
            raise LocalizationError("Localization validation failed. Check the logs for details.")
        else:
            cls.locales = locales
            logging.info("Available locales: " + ", ".join(locales))
            logging.info("All localization files are valid.")