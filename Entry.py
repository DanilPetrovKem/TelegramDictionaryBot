from typing import List

class Etymology:
    def __init__(self):
        self.lexemes: List[Lexeme] = []
    # Changed __repr__ for tree-like structure using two spaces instead of tabs
    def __repr__(self):
        lexemes_repr = "\n".join("  " + repr(lex).replace("\n", "\n  ") for lex in self.lexemes) if self.lexemes else "  None"
        return f"Etymology:\n  lexemes:\n{lexemes_repr}"

class Lexeme:
    def __init__(self):
        self.lemma: str = ""
        self.part_of_speech: str = ""
        self.senses: List[Sense] = []
    # Changed __repr__ for tree-like structure using two spaces instead of tabs
    def __repr__(self):
        senses_repr = "\n".join("  " + repr(sense).replace("\n", "\n  ") for sense in self.senses) if self.senses else "  None"
        return (f"Lexeme:\n  lemma: {self.lemma}\n  part_of_speech: {self.part_of_speech}\n  senses:\n{senses_repr}")

class Sense:
    def __init__(self):
        self.definition: str = ""
        self.labels: List[str] = []
        self.examples: List[str] = []
        self.synonyms: List[str] = []
        self.antonyms: List[str] = []
        self.collocations: List[str] = []
        self.subsenses: List[Sense] = []
    # Changed __repr__ for tree-like structure using two spaces instead of tabs
    def __repr__(self):
        subsenses_repr = "\n".join("  " + repr(sub).replace("\n", "\n  ") for sub in self.subsenses) if self.subsenses else "  None"
        return (f"Sense:\n  definition: {self.definition}\n  labels: {self.labels}\n  examples: {self.examples}\n"
                f"  synonyms: {self.synonyms}\n  antonyms: {self.antonyms}\n  collocations: {self.collocations}\n  "
                f"subsenses:\n{subsenses_repr}")

class Entry:
    def __init__(self):
        self.redirected: bool = False
        self.entry: str = ""
        self.etymologies: List[Etymology] = []
        
    def lexeme_amount(self) -> int:
        return sum(len(etymology.lexemes) for etymology in self.etymologies)
    
    def get_lexeme_by_index(self, index: int) -> Lexeme:
        for etymology in self.etymologies:
            if index < len(etymology.lexemes):
                return etymology.lexemes[index]
            index -= len(etymology.lexemes)
        return None
        
    # Changed __repr__ for tree-like structure using two spaces instead of tabs
    def __repr__(self):
        etymologies_repr = "\n".join("  " + repr(ety).replace("\n", "\n  ") for ety in self.etymologies) if self.etymologies else "  None"
        return (f"Entry:\n  redirected: {self.redirected}\n  entry: {self.entry}\n  etymologies:\n{etymologies_repr}")
