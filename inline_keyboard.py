from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from localization import Localization
from localization_keys import Phrases
from enums import UserData

class LexemeButton(str):
    def __new__(cls, lexeme_number: int):
        return str.__new__(cls, f"lexeme-{lexeme_number}")

class Button(str, Enum):
    MORE_DETAILS = "more_details"

    ALL_DEFINITIONS = "all_definitions"

    SYNONYMS = "synonyms"
    ANTONYMS = "antonyms"
    RHYMES = "rhymes"

    CLOSE = "close"

    @staticmethod
    def lexemes(lexeme_numbers: int) -> list[LexemeButton]:
        return [LexemeButton(i) for i in range(1, lexeme_numbers + 1)]
    
    @staticmethod
    def is_lexeme(button: str) -> bool:
        return button.startswith("lexeme")

class InlineKeyboard:
    @staticmethod
    def generate(button_table: list[list], localization: Localization) -> InlineKeyboardMarkup:
        keyboard_buttons = []
        for button_list in button_table:
            row = []
            for button in button_list:
                if button in Phrases:
                    phrase_key = Phrases[button]
                    b_text = localization.get(phrase_key)
                elif Button.is_lexeme(button):
                    b_text = f"{button.split('-')[1]}"
                else:
                    b_text = button.replace("_", " ").title()
                row.append(InlineKeyboardButton(b_text, callback_data=button))
            keyboard_buttons.append(row)
        return InlineKeyboardMarkup(keyboard_buttons)

    @staticmethod
    def generate_details_buttons(user_data, localization: Localization, lexeme_amount: int) -> InlineKeyboardMarkup:
        used_buttons = user_data.get(UserData.USED_BUTTONS, [])
        button_structure = []
        
        if not used_buttons:
            # Layer 1
            # User can restrict to a lexeme
            if lexeme_amount > 1:
                button_structure.append(Button.lexemes(lexeme_amount))
            button_structure.append([Button.CLOSE])

        # If any of the buttons is a LexemeButton
        elif is_lexeme_chosen(used_buttons):
            # Layer 2
            button_structure = [
                [Button.ALL_DEFINITIONS],
                [Button.SYNONYMS, Button.ANTONYMS],
                [Button.RHYMES],
                [Button.CLOSE]
            ]
        else:
            button_structure = []

        unused_buttons = []
        for row in button_structure:
            filtered_row = [button for button in row if button not in used_buttons]
            if filtered_row:
                unused_buttons.append(filtered_row)

        # If only the close button is left, remove the entire row
        if len(unused_buttons) == 1 and len(unused_buttons[0]) == 1:
            unused_buttons = []
        return InlineKeyboard.generate(unused_buttons, localization)
    
def is_lexeme_chosen(used_buttons) -> bool:
    return any(Button.is_lexeme(button) for button in used_buttons)