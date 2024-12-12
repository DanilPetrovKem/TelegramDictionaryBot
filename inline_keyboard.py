from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from localization import Localization
from localization_keys import Phrases

class Buttons(Enum):
    MORE_DETAILS = "more_details"
    SYNONYMS = "synonyms"
    ANTONYMS = "antonyms"
    CLOSE = "close"

    @property
    def callback_data(self):
        return self.value

class InlineKeyboard:
    @staticmethod
    def generate(buttons, localization: Localization) -> InlineKeyboardMarkup:
        keyboard_buttons = []
        for button in buttons:
            if isinstance(button, Buttons):
                try:
                    # Map Buttons enum to Phrases enum using button name
                    phrase_key = Phrases[button.name]  # Phrases enum should have the same member names
                    button_text = localization.get(phrase_key)
                except KeyError:
                    # Handle the case where the phrase does not exist
                    button_text = button.name.replace("_", " ").title()
                keyboard_buttons.append([InlineKeyboardButton(button_text, callback_data=button.callback_data)])
            elif isinstance(button, list):
                row = []
                for b in button:
                    try:
                        phrase_key = Phrases[b.name]
                        b_text = localization.get(phrase_key)
                    except KeyError:
                        b_text = b.name.replace("_", " ").title()
                    row.append(InlineKeyboardButton(b_text, callback_data=b.callback_data))
                keyboard_buttons.append(row)
        return InlineKeyboardMarkup(keyboard_buttons)