from typing import List

def clean_unsupported_tags(text: str) -> str:
    text = text.replace("<math>", "").replace("</math>", "")
    return text

class Etymology:
    def __init__(self):
        self.lexemes: List[Lexeme] = []

    @classmethod
    def from_json(cls, data: dict) -> 'Etymology':
        inst = cls()
        inst.lexemes = [Lexeme.from_json(item) for item in data.get("lexemes", [])]
        return inst

    # Changed __repr__ for tree-like structure using two spaces instead of tabs
    def __repr__(self):
        lexemes_repr = "\n".join("  " + repr(lex).replace("\n", "\n  ") for lex in self.lexemes) if self.lexemes else "  None"
        return f"Etymology:\n  lexemes:\n{lexemes_repr}"

class Lexeme:
    def __init__(self):
        self.lemma: str = ""
        self.part_of_speech: str = ""
        self.senses: List[Sense] = []

    @classmethod
    def from_json(cls, data: dict) -> 'Lexeme':
        inst = cls()
        inst.lemma = data.get("lemma") or ""
        inst.part_of_speech = data.get("part_of_speech") or ""
        inst.senses = [Sense.from_json(s) for s in data.get("senses", [])]
        return inst

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

    @classmethod
    def from_json(cls, data: dict) -> 'Sense':
        inst = cls()
        inst.definition = clean_unsupported_tags(data.get("definition") or "")
        inst.labels = [clean_unsupported_tags(label) for label in data.get("labels", [])]
        inst.examples = [clean_unsupported_tags(example) for example in data.get("examples", [])]
        inst.synonyms = [clean_unsupported_tags(synonym) for synonym in data.get("synonyms", [])]
        inst.antonyms = [clean_unsupported_tags(antonym) for antonym in data.get("antonyms", [])]
        inst.collocations = [clean_unsupported_tags(collocation) for collocation in data.get("collocations", [])]
        inst.subsenses = [cls.from_json(sub) for sub in data.get("subsenses", [])]
        return inst

    def get_definition_with_labels(self) -> str:
        return f"{self.definition} ({', '.join(self.labels)})" if self.labels else self.definition
    
    # Changed __repr__ for tree-like structure using two spaces instead of tabs
    def __repr__(self):
        subsenses_repr = "\n".join("  " + repr(sub).replace("\n", "\n  ") for sub in self.subsenses) if self.subsenses else "  None"
        return (f"Sense:\n  definition: {self.definition}\n  labels: {self.labels}\n  examples: {self.examples}\n"
                f"  synonyms: {self.synonyms}\n  antonyms: {self.antonyms}\n  collocations: {self.collocations}\n  "
                f"subsenses:\n{subsenses_repr}")

class Entry:
    def __init__(self):
        self.redirected_from: str = ""
        self.entry: str = ""
        self.etymologies: List[Etymology] = []
        
    @classmethod
    def from_json(cls, data: dict) -> 'Entry':
        inst = cls()
        inst.redirected_from = data.get("redirected_from") or ""
        inst.entry = data.get("entry") or ""
        inst.etymologies = [Etymology.from_json(ety) for ety in data.get("etymologies", [])]
        return inst
    
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
        return (f"Entry:\n  redirected_from: {self.redirected_from}\n  entry: {self.entry}\n  etymologies:\n{etymologies_repr}")
