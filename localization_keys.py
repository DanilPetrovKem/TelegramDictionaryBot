from enum import Enum, auto

class Phrases(Enum):
    # Messages
    START_MESSAGE = auto()
    HELP_MESSAGE = auto()
    CANCEL_MESSAGE = auto()
    
    # Buttons
    MORE_DETAILS = auto()
    ALL_DEFINITIONS = auto()
    SYNONYMS = auto()
    ANTONYMS = auto()
    RHYMES = auto()
    CLOSE = auto()

    # Command replies
    LANGUAGE_CHANGED = auto()
    
    # Command annotations
    COMMAND_RANDOM = auto()
    COMMAND_LANG_EN = auto()
    COMMAND_LANG_RU = auto()
    COMMAND_HELP = auto()

    # Errors
    WORD_NOT_FOUND = auto()
    NO_DEFINITIONS_FOUND = auto()
    
    UNKNOWN_ACTION = auto()
    INVALID_COMMAND_USAGE = auto()
    INVALID_LANGUAGE = auto()