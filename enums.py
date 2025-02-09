from enum import Enum

class UserData(str, Enum):
    ENTRY = "entry"
    USED_BUTTONS = "used_buttons"
    LOCALE = "locale"
    LAST_MESSAGE_ID = "last_message_id"
    DEFINITIONS_REQUESTED = "definitions_requested"

# class MessageResult(str, Enum):
#     OK = "ok"
#     NOT_FOUND = "word_not_found"
#     NO_DEFINITIONS = "no_definitions_found"