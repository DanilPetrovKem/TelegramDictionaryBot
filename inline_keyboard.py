from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from localization import Localization
from localization_keys import Phrases

class Button(Enum):
    MORE_DETAILS = "more_details"

    ALL_DEFINITIONS = "all_definitions"

    SYNONYMS = "synonyms"
    ANTONYMS = "antonyms"
    RHYMES = "rhymes"

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
        button_structure = [
            [Button.ALL_DEFINITIONS],
            [Button.SYNONYMS, Button.ANTONYMS],
            [Button.RHYMES],
            [Button.CLOSE]
        ]
        unused_buttons = []
        for row in button_structure:
            filtered_row = [button for button in row if button.value not in used_buttons]
            if filtered_row:
                unused_buttons.append(filtered_row)

        # If only the close button is left, remove the entire row
        if len(unused_buttons) == 1 and len(unused_buttons[0]) == 1:
            unused_buttons = []
        return InlineKeyboard.generate(unused_buttons, localization)