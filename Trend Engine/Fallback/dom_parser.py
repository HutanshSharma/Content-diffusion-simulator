import json
from pathlib import Path
from datetime import datetime,UTC
from scraper import scraper

class DocumentEncoder:
    def generic_extractor(self, soup):
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

    def reddit_extractor(self, soup):
        data=soup.find("shreddit-feed")
        output=[]
        extraction_time = datetime.now(UTC).strftime("%Y-%m-%d_%H.%M.%S") 
        if data:
            posts=data.find_all("shreddit-post")
            for post in posts:
                title=post.get("post-title") if post.has_attr("post-title") else ""
                id=post.get("id") if post.has_attr("id") else ""
                upvotes=post.get("score") if post.has_attr("score") else 0
                subreddit=post.get("subreddit-name") if post.has_attr("subreddit-name") else ""
                comments=post.get("comment-count") if post.has_attr("comment-count") else 0
                created_utc=post.get("created-timestamp") if post.has_attr("created-timestamp") else ""
                formatted = datetime.strptime(created_utc,"%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d_%H.%M.%S") if created_utc else ""

                if id and title:
                    output.append({
                    "id":id,
                    "title":title,
                    "source":"reddit",
                    "region":"IN",
                    "feed":"popular",
                    "subreddit":subreddit,
                    "created_utc":formatted,
                    "extracted_utc":extraction_time,
                    "upvotes":upvotes,
                    "comments":comments
                })
        return output
        

    def youtube_extractor(self, soup):
        pass


    def save(self,data,name):
        BASE_DIR = Path(__file__).resolve().parent
        dir=(BASE_DIR.parent.parent/"data"/"raw")
        dir.mkdir(parents=True, exist_ok=True)
        filename = datetime.now(UTC).strftime(f"%Y-%m-%d_%H-%M-%S-scraper {name}.json")

        filepath=dir/filename

        with open(filepath,"w",encoding="utf-8") as f:
            json.dump(data,f,indent=4)

if __name__=="__main__":
    encoder = DocumentEncoder()
    data=scraper("https://www.reddit.com/r/popular/",encoder.reddit_scrapper)
    encoder.save(data,"reddit")
