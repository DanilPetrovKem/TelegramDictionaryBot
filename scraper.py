import requests
from bs4 import BeautifulSoup
import re
import json
import os
from Entry import Entry, Etymology, Lexeme, Sense

class WiktionaryScraper:
    entries_folder = "entries"

    def fetch(self, entry) -> Entry:
        url = f"https://en.wiktionary.org/wiki/{entry}"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            entry = self.process_full_page(soup)
            return entry
        else:
            print(f"Failed to retrieve the page for {entry}")

    def process_full_page(self, soup: BeautifulSoup) -> Entry:
        content = self.extract_content(soup)
        english_section = self.extract_english_section(content)
        entry = self.convert_to_object(english_section)
        return entry

    def extract_content(self, soup: BeautifulSoup):
        content = soup.find('div', class_='mw-content-ltr mw-parser-output')
        return content

    def extract_english_section(self, soup: BeautifulSoup):
        english_div = None
        headings = soup.find_all("div", class_="mw-heading mw-heading2")
        for heading in headings:
            h2_tag = heading.find("h2", id="English")
            if h2_tag:
                english_div = heading
                break
        if not english_div:
            return None
        content_tags = []
        for sibling in english_div.find_next_siblings():
            if sibling.name == "div" and "mw-heading2" in sibling.get("class", []):
                break
            content_tags.append(sibling)
        english_section = BeautifulSoup("<div></div>", "html.parser")
        container = english_section.div
        for tag in content_tags:
            container.append(tag)
        # self.write_to_html(english_section, "english_section")
        return english_section
    
    def convert_to_object(self, soup: BeautifulSoup) -> Entry:
        etymology_contents = []
        entry = Entry()

        etymology_headings = []
        headings = soup.find_all('div', class_='mw-heading mw-heading3')
        for heading in headings:
            if heading.text.startswith("Etymology"):
                etymology_headings.append(heading)
        
        for etymology_heading in etymology_headings:
                etymology_content = BeautifulSoup("<div></div>", "html.parser")
                for sibling in etymology_heading.find_next_siblings():
                    if sibling.name == "div" and "mw-heading3" in sibling.get("class", []) and sibling.text.startswith("Etymology"):
                        break
                    etymology_content.div.append(sibling)
                etymology_contents.append(etymology_content)
        
        if len(etymology_contents) == 1:
            etymology = self.process_etymology(etymology_contents[0], single=True)
            entry.etymologies.append(etymology)
        else:
            for etymology_content in etymology_contents:
                etymology = self.process_etymology(etymology_content)
                entry.etymologies.append(etymology)

        return entry


    def process_etymology(self, soup: BeautifulSoup, single=False) -> Etymology:
        etymology = Etymology()
        lexeme_div_class = "mw-heading mw-heading3" if single else "mw-heading mw-heading4"
        POS_tag = "h3" if single else "h4"
        lexemes_divs = soup.find_all('div', class_=lexeme_div_class)
        for lexeme_div in lexemes_divs:
            headword = lexeme_div.find_next(class_="headword-line")
            if headword == None: continue
            if lexeme_div.find(POS_tag).text.lower() == "pronunciation": continue

            lexeme = Lexeme()
            lexeme.lemma = headword.strong.text
            lexeme.part_of_speech = lexeme_div.find(POS_tag).text.lower()

            sense_list = lexeme_div.find_next("ol")
            senses = sense_list.find_all("li")
            for sense in senses:
                if not sense.text: continue
                for child in sense.children:
                    if child.name == "dl" or child.name == "ul" or child.name == "ol":
                        child.decompose()
                definition_text = sense.text.split("\n")[0].strip()
                definition_text = self.format(definition_text)
                sense_object = Sense()
                sense_object.definition = definition_text
                lexeme.senses.append(sense_object)

            etymology.lexemes.append(lexeme)

        return etymology
    
    def format(self, text):
        text = text.replace("\u00a0", " ")
        text = text.replace("\u201c", "\"")
        text = text.replace("\u201d", "\"")
        text = re.sub(r"\[\d+\]", "", text)
        return text

    def write_to_html(self, soup, filename):
        os.makedirs(self.entries_folder, exist_ok=True)
        with open(f"{self.entries_folder}/{filename}.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
    
    def write_to_json(self, data, filename):
        os.makedirs(self.entries_folder, exist_ok=True)
        with open(f"{self.entries_folder}/{filename}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def test_fetch(self, entry):
        result = self.fetch(entry)
        # self.write_to_json(result, entry)


if __name__ == "__main__":
    scraper = WiktionaryScraper()
    scraper.test_fetch("ball")
    # scraper.test_fetch("white")
    # scraper.test_fetch("shove")
    # scraper.test_fetch("run")
    # scraper.test_fetch("jump")
    # scraper.test_fetch("cow")
