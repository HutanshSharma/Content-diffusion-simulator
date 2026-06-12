# import json
# from pathlib import Path
# from pytrends.request import TrendReq
# import feedparser
# from datetime import datetime, UTC

# class GoogleTrendsCollector:
#     def __init__(self, region: str = "US", language: str = "en-US"):
#         self.region = region
#         self.language = language
#         self.pytrends = TrendReq(hl=self.language, tz=0)
    
#     def collect(self) -> list[dict]:
#         extraction_time = datetime.now(UTC).strftime("%Y-%m-%d_%H.%M.%S")
#         posts = []
 
#         feeds = [
#             ("realtime", self._collect_realtime()),
#             # ("daily",    self._collect_daily()),
#         ]

#         for feed_name, items in feeds:
#             for item in items:
#                 item.update({
#                     "source":        "google_trends",
#                     "region":        self.region,
#                     "feed":          feed_name,
#                     "extracted_utc": extraction_time,
#                 })
#                 posts.append(item)
 
#         return posts
    
#     def _collect_realtime(self) -> list[dict]:
#         """Realtime trending searches (returns ~25 stories)."""
#         results = []
#         try:
#             df = self.pytrends.realtime_trending_searches(pn=self.region)
#             for _, row in df.iterrows():
#                 results.append({
#                     "id":          str(row.get("id", "")),
#                     "title":       row.get("title", ""),
#                     "articles":    row.get("articles", []),
#                     "image":       row.get("image", {}).get("imageUrl", "") if isinstance(row.get("image"), dict) else "",
#                     "created_utc": "",          # not provided by realtime feed
#                     "traffic":     row.get("formattedTraffic", ""),
#                 })
#         except Exception as e:
#             print(f"[GoogleTrendsCollector] realtime feed error: {e}")
#         return results
    
#     def _collect_daily(self):

#         url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={self.region}"

#         feed = feedparser.parse(url)

#         results = []

#         for entry in feed.entries:
#             results.append({
#                 "id": "",
#                 "title": entry.title,
#                 "articles": [],
#                 "image": "",
#                 "created_utc": "",
#                 "traffic": ""
#             })

#         return results
    
#     def save(self, posts: list[dict]) -> None:
#         dir = Path("../../data/raw")
#         dir.mkdir(parents=True, exist_ok=True)
#         filename = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S-google_trends.json")
#         filepath = dir / filename
#         with open(filepath, "w", encoding="utf-8") as f:
#             json.dump(posts, f, indent=4)
#         print(f"[GoogleTrendsCollector] Saved {len(posts)} items → {filepath}")

# if __name__ == "__main__":
#     collector = GoogleTrendsCollector(region="IN")
#     posts = collector.collect()
#     collector.save(posts)



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

        print(f"[GoogleTrendsCollector] Collected {len(results)} trends")

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

        print(
            f"[GoogleTrendsCollector] Saved {len(posts)} items → {filepath}"
        )


if __name__ == "__main__":
    collector = GoogleTrendsCollector(region="IN")

    posts = collector.collect()

    collector.save(posts)