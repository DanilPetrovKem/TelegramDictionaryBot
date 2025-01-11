from typing import List

class Etymology:
    def __init__(self):
        self.lexemes: List[Lexeme] = []

class Lexeme:
    def __init__(self):
        self.lemma: str = ""
        self.part_of_speech: str = ""
        self.senses: List[Sense] = []

class Sense:
    def __init__(self):
        self.definition: str = ""


class Entry:
    def __init__(self):
        self.etymologies: List[Etymology] = []

    def lexeme_amount(self) -> int:
        return sum(len(etymology.lexemes) for etymology in self.etymologies)
    
    def get_lexeme_by_index(self, index: int) -> Lexeme:
        for etymology in self.etymologies:
            if index < len(etymology.lexemes):
                return etymology.lexemes[index]
            index -= len(etymology.lexemes)
        return None


