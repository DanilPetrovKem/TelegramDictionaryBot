from enum import Enum

class ContextKey(str, Enum):
    DATA = "data"
    USED_BUTTONS = "used_buttons"
    LOCALE = "locale"
    LAST_MESSAGE_ID = "last_message_id"