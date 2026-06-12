import json
from pathlib import Path
from datetime import datetime,UTC
from scraper import scraper

class DocumentEncoder:
    def extract(self, soup):
        title = ""
        if soup.title:
            title = soup.title.get_text(" ",strip=True)

        summary = ""
        meta_description = soup.find("meta",attrs={"name": "description"})
        if meta_description:
            summary = meta_description.get("content","")
        headings = []

        for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
            text = tag.get_text(" ",strip=True)
            if text:
                headings.append(text)

        paragraphs = []

        for tag in soup.find_all("p"):
            text = tag.get_text(" ",strip=True)
            if text and len(text) > 20:
                paragraphs.append(text)

        links = []

        for tag in soup.find_all("a",href=True):
            href = tag["href"]
            if href:
                links.append(href)

        raw_sections = (headings+paragraphs)
        main_text = "\n".join(raw_sections)

        metadata = {
            "heading_count":len(headings),
            "paragraph_count":len(paragraphs),
            "link_count":len(links),
            "word_count":len(main_text.split())
        }
        return {
            "source_type": "html",
            "title": title,
            "summary": summary,
            "main_text": main_text,
            "search_text":f"{title}\n{summary}\n{main_text}",
            "raw_sections": raw_sections,
            "links": links,
            "metadata": metadata
        }

    def save(self,data):
        BASE_DIR = Path(__file__).resolve().parent
        dir=(BASE_DIR.parent.parent/"data"/"raw")
        dir.mkdir(parents=True, exist_ok=True)
        filename = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S-scraper.json")

        filepath=dir/filename

        with open(filepath,"w",encoding="utf-8") as f:
            json.dump(data,f,indent=4)

if __name__=="__main__":
    encoder = DocumentEncoder()
    data=scraper("https://www.reddit.com/",encoder.extract)
    encoder.save(data)
