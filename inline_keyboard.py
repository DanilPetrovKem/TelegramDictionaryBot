from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from localization import Localization
from localization_keys import Phrases

class Button(Enum):
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
            if isinstance(button, Button):
                try:
                    phrase_key = Phrases[button.name]
                    button_text = localization.get(phrase_key)
                except KeyError:
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

    @staticmethod
    def generate_details_buttons(user_data, localization: Localization) -> InlineKeyboardMarkup:
        used_buttons = user_data.get('used_buttons', [])
        unused_buttons = [
            button for button in [Button.SYNONYMS, Button.ANTONYMS]
            if button.value not in used_buttons
        ]
        if not unused_buttons:
            return None
        return InlineKeyboard.generate([
            unused_buttons,
            [Button.CLOSE]
        ], localization)