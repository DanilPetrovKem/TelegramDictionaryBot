from enum import Enum

class UserData(str, Enum):
    ENTRY = "entry"
    USED_BUTTONS = "used_buttons"
    LOCALE = "locale"
    LAST_MESSAGE_ID = "last_message_id"
    DEFINITIONS_REQUESTED = "definitions_requested"