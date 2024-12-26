import requests
from bs4 import BeautifulSoup
import re
import json

class WiktionaryScraper:
    entries_folder = "entries"

    def fetch(self, entry) -> dict:
        url = f"https://en.wiktionary.org/wiki/{entry}"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            result = self.process_full_page(soup)
            return result
        else:
            print(f"Failed to retrieve the page for {entry}")

    def process_full_page(self, soup: BeautifulSoup):
        content = self.extract_content(soup)
        english_section = self.extract_english_section(content)
        result_dict = self.convert_to_dict(english_section)
        return result_dict

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
        parent = BeautifulSoup("<div></div>", "html.parser")
        container = parent.div
        for tag in content_tags:
            container.append(tag)
        return parent
    
    def convert_to_dict(self, soup: BeautifulSoup) -> dict:
        result_dict = {}
        result_dict["etymologies"] = self.process_etymologies(soup)
        return result_dict

    def process_etymologies(self, soup: BeautifulSoup):
        print(soup)
        lexemes_list = []
        etymology_divs = []
        headings = soup.find_all('div', class_='mw-heading mw-heading3')
        for heading in headings:
            if heading.find(id=re.compile(r'^Etymology')):
                etymology = heading
                etymology_divs.append(etymology)

        if len(etymology_divs) == 1:
            print("Single etymology")
            etymology_content = BeautifulSoup("<div></div>", "html.parser")
            container = etymology_content.div
            print(etymology_divs[0].find_next_siblings())
            for tag in etymology_divs[0].find_next_siblings():
                if tag.name == "div" and "mw-heading3" in tag.get("class", []):
                    break
                container.append(tag)
            lexemes = self.process_etymology(etymology_content, single=True)
            lexemes_list.append(lexemes)
            return lexemes_list
        else:
            print("Multiple etymologies")
            for etymology in etymology_divs:
                content_tags = []
                print(etymology.find_next_siblings())
                for sibling in etymology.find_next_siblings():
                    if sibling.name == "div" and "mw-heading3" in sibling.get("class", []):
                        break
                    content_tags.append(sibling)
                etymology_content = BeautifulSoup("<div></div>", "html.parser")
                container = etymology_content.div
                for tag in content_tags:
                    container.append(tag)
                lexemes = self.process_etymology(etymology_content)
                lexemes_list.append(lexemes)

            return lexemes_list


    def process_etymology(self, soup: BeautifulSoup, single=False) -> dict:
        print(soup)
        lexemes = []
        # Find divs with mw-heading mw-heading* class
        if single:
            lexemes_divs = soup.find_all('div', class_='mw-heading mw-heading3')
        else:
            lexemes_divs = soup.find_all('div', class_='mw-heading mw-heading4')

        for lexeme_div in lexemes_divs:
            # Find next class headword-line
            headword = lexeme_div.find_next(class_="headword-line")
            if headword == None: continue

            lexeme_dict = {}
            lexeme_dict["lemma"] = headword.strong.text
            lexeme_dict["partOfSpeech"] = lexeme_div.h4.text.lower()

            sense_list = lexeme_div.find_next("ol")
            senses = sense_list.find_all("li")
            lexeme_dict["senses"] = []
            for sense in senses:
                if not sense.text: continue
                for child in sense.children:
                    if child.name == "dl" or child.name == "ul" or child.name == "ol":
                        child.decompose()
                definition_text = sense.text.split("\n")[0].strip()
                definition_text = self.format(definition_text)
                lexeme_dict["senses"].append({"definition": definition_text})

            lexemes.append(lexeme_dict)

        return lexemes
    
    def format(self, text):
        text = text.replace("\u00a0", " ")
        return text

if __name__ == "__main__":
    scraper = WiktionaryScraper()
    # ball = scraper.fetch("ball")
    # with open("scraper_tests/ball.json", "w", encoding="utf-8") as f:
    #     json.dump(ball, f, indent=4)

    white = scraper.fetch("white")
    with open("scraper_tests/white.json", "w", encoding="utf-8") as f:
        json.dump(white, f, indent=4)