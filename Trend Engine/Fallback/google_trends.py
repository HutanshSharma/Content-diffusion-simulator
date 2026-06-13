import json
from pathlib import Path
from datetime import datetime, UTC

import feedparser

class GoogleTrendsCollector:
    def __init__(self, region="IN"):
        self.region = region

    def _collect_daily(self):
        url = f"https://trends.google.com/trending/rss?geo={self.region}"

        feed = feedparser.parse(url)

        results = []

        for entry in feed.entries:
            results.append({
                "id": "",
                "title": entry.title,
                "articles": [],
                "image": "",
                "created_utc": "",
                "traffic": "",
            })

        return results

    def collect(self):
        extraction_time = datetime.now(UTC).strftime("%Y-%m-%d_%H.%M.%S")

        posts = []

        for item in self._collect_daily():
            item.update({
                "source": "google_trends",
                "region": self.region,
                "feed": "daily",
                "extracted_utc": extraction_time,
            })

            posts.append(item)

        return posts

    def save(self, posts):
        BASE_DIR = Path(__file__).resolve().parents[2]
        output_dir = BASE_DIR / "data" / "raw"
        output_dir.mkdir(parents=True, exist_ok=True)      

        filename = datetime.now(UTC).strftime(
            "%Y-%m-%d_%H-%M-%S-google_trends.json"
        )

        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=4)


if __name__ == "__main__":
    collector = GoogleTrendsCollector(region="IN")
    posts = collector.collect()
    collector.save(posts)