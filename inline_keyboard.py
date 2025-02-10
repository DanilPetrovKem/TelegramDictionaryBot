from enum import Enum, auto
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from localization import Localization
from localization_keys import Phrases
from enums import UserData

class LexemeButton(str):
    def __new__(cls, lexeme_number: int):
        return str.__new__(cls, f"lexeme-{lexeme_number}")

class Button(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.upper()
    MORE_DETAILS = auto()

    MORE_DEFINITIONS = auto()
    LESS_DEFINITIONS = auto()
    DEFINITIONS_BORDER = auto()

    EXAMPLES = auto()
    SYNONYMS = auto()
    ANTONYMS = auto()
    RHYMES = auto()

    CLOSE = auto()

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
        # Remove Button.DEFINITIONS_BORDER if it's there
        if Button.DEFINITIONS_BORDER in used_buttons:
            used_buttons.remove(Button.DEFINITIONS_BORDER)
        
        button_structure = []
        if not used_buttons and lexeme_amount > 1:
            # Layer 1
            # Buttons for choosing a specific lexeme
            # print("Layer 1")
            if lexeme_amount > 1:
                lexeme_buttons = Button.lexemes(lexeme_amount)
                for i in range(0, len(lexeme_buttons), 5):
                    button_structure.append(lexeme_buttons[i:i + 5])

            button_structure.append([Button.CLOSE])

        # If single lexeme
        elif is_lexeme_chosen(used_buttons) or lexeme_amount == 1:
            # Layer 2
            # print("Layer 2")
            chosen_lexeme = get_lexeme_chosen_id(used_buttons) if is_lexeme_chosen(used_buttons) else 0
            definitions_required = user_data.get(UserData.DEFINITIONS_REQUESTED, 1)
            entry = user_data.get(UserData.ENTRY)
            lexeme = entry.get_lexeme_by_index(chosen_lexeme)
            examples_available = any(sense.examples for sense in lexeme.senses[:definitions_required])
            sense_amount = len(lexeme.senses)
            sense_amount_buttons = []
            if sense_amount > 1:
                if definitions_required != 1:
                    sense_amount_buttons.append(Button.LESS_DEFINITIONS)
                else:
                    sense_amount_buttons.append(Button.DEFINITIONS_BORDER)
                if definitions_required != sense_amount:
                    sense_amount_buttons.append(Button.MORE_DEFINITIONS)
                else:
                    sense_amount_buttons.append(Button.DEFINITIONS_BORDER)
            button_structure = [
                sense_amount_buttons if sense_amount > 1 else [],
                # [Button.SYNONYMS, Button.ANTONYMS],
                [Button.EXAMPLES] if examples_available else [],    
                [Button.CLOSE]
            ]
        else:
            # print("FALLBACK")
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

def get_lexeme_chosen_id(used_buttons) -> int:
    for button in used_buttons:
        if Button.is_lexeme(button):
            return int(button.split('-')[1]) - 1
    return None