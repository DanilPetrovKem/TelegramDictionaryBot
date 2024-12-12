from enum import Enum, auto

class Phrases(Enum):
    START_MESSAGE = auto()
    HELP_MESSAGE = auto()
    CANCEL_MESSAGE = auto()
    WORD_NOT_FOUND = auto()
    NO_DEFINITIONS_FOUND = auto()
    NO_SYNONYMS_FOUND = auto()
    NO_ANTONYMS_FOUND = auto()
    UNKNOWN_ACTION = auto()
    MORE_DETAILS = auto()
    SYNONYMS = auto()
    ANTONYMS = auto()
    CLOSE = auto()
    MAIN_MEANING = auto()