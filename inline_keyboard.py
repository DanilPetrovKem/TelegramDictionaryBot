from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class Buttons(Enum):
    MORE_DETAILS = "More details"
    SYNONYMS = "Synonyms"
    ANTONYMS = "Antonyms"
    CLOSE = "Close"

    @property
    def callback_data(self):
        return self.name.lower()

class InlineKeyboard:
    @staticmethod
    def generate(buttons):
        if all(isinstance(button, Buttons) for button in buttons):
            # Single row keyboard
            keyboard_buttons = [
                [InlineKeyboardButton(button.value, callback_data=button.callback_data) for button in buttons]
            ]
        elif all(isinstance(row, list) for row in buttons):
            # Multiple rows
            keyboard_buttons = [
                [InlineKeyboardButton(button.value, callback_data=button.callback_data) for button in row]
                for row in buttons
            ]
        else:
            raise ValueError("Invalid format for buttons. Provide a list of Buttons or list of list of Buttons.")

        return InlineKeyboardMarkup(keyboard_buttons)