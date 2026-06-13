import os
import json
from pathlib import Path
from datetime import datetime,UTC
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

youtube=build(
    serviceName="youtube",
    version="v3",
    developerKey=os.getenv("YOUTUBE_API_KEY")
)

class YoutubeCollector:
    def collect(self,region="IN",limit=50):
        request=youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode=region,
            maxResults=limit
        )
        response = request.execute()
        videos=[]

        extraction_time = datetime.now(UTC).strftime("%Y-%m-%d_%H.%M.%S")

        for item in response["items"]:
            snippet=item["snippet"]
            stats=item["statistics"]
            videos.append({
                "id":item['id'],
                "title":snippet["title"],
                "description":snippet["description"],
                "channel":snippet["channelTitle"],
                "category_id":snippet["categoryId"],
                "published_at":snippet["publishedAt"],
                "region":region,
                "source":"youtube",
                "views":stats.get("viewCount",0),
                "likes":stats.get("likeCount",0),
                "comments":stats.get("commentCount",0),
                "extracted_utc":extraction_time
            })
        return videos
    
    def save(self,data):
        BASE_DIR = Path(__file__).resolve().parent
        dir=(BASE_DIR.parent.parent/"data"/"raw")
        dir.mkdir(parents=True, exist_ok=True)
        # filename = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S-youtube.json")
        filename = datetime.now(UTC).strftime("youtube.json")

        filepath=dir/filename

        with open(filepath,"w",encoding="utf-8") as f:
            json.dump(data,f,indent=4)

if __name__=="__main__":
    collector=YoutubeCollector()
    videos=collector.collect(region="US",limit=50)
    collector.save(videos)
