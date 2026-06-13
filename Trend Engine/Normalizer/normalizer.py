import json
from pathlib import Path
from Processors import Processor
import hashlib

class Normalizer:
    def _generate_id(self,source,created_utc):
        text = (f"{source}|"f"{created_utc}")
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def normalize_reddit(self,raw_data,processed_data):
        normalized = []
        for raw, processed in zip(raw_data,processed_data):
            normalized.append({
                "id": self._generate_id(
                    raw["source"],
                    raw["created_utc"],
                ),
                "source": raw["source"],
                "region": raw["region"],
                "created_utc": raw["created_utc"],
                "extracted_utc": raw["extracted_utc"],
                "tags": processed["tags"],
                "keywords": processed["keywords"],
                "interactions": [
                    raw["upvotes"],
                    raw["comments"]
                ]
            })

        return normalized

    def normalize_youtube(self,raw_data,processed_data):
        normalized = []
        for raw, processed in zip(raw_data,processed_data):
            normalized.append({
                "id": self._generate_id(
                    raw["source"],
                    raw["published_at"],
                ),
                "source": raw["source"],
                "region": raw["region"],
                "created_utc": raw["published_at"],
                "extracted_utc": raw["extracted_utc"],
                "tags": processed["tags"],
                "keywords": processed["keywords"],
                "interactions": [
                    int(raw["views"]),
                    int(raw["likes"]),
                    int(raw["comments"])
                ]
            })

        return normalized

    def normalize_google_trends(self,raw_data,processed_data):
        normalized = []

        for raw, processed in zip(raw_data,processed_data):
            normalized.append({
                "id": self._generate_id(
                    raw["source"],
                    raw["Started"],
                ),
                "source": raw["source"],
                "region": raw["region"],
                "created_utc": raw["Started"],
                "extracted_utc": raw["extraction_utc"],
                "tags": processed["tags"],
                "keywords": processed["keywords"],
                "interactions": [
                    raw["Search volume"]
                ]
            })

        return normalized

if __name__=="__main__":
    BASE_DIR = Path(__file__).resolve().parent
    dir=(BASE_DIR.parent.parent/"data"/"raw")

    with open(f"{dir}/reddit.json","r",encoding="utf-8") as f:
        reddit_data = json.load(f)

    processor = Processor()

    processed_reddit = processor.process(
        reddit_data,
        primary_field="title",
        secondary_field="subreddit_description",
        description_field="post_description"
    )

    with open(f"{dir}/youtube.json","r",encoding="utf-8") as f:
        yt_data = json.load(f)

    processor = Processor()

    processed_yt = processor.process(
        yt_data,
        primary_field="title",
        secondary_field="description",
        description_field="description"
    )

    with open(f"{dir}/google-trends.json","r",encoding="utf-8") as f:
        trends_data=json.load(f)

    processed_trends = processor.process(
        trends_data,
        primary_field="Trends",
        secondary_field="Trend breakdown",
        description_field="Trend breakdown"
    ) 

    normalizer = Normalizer()
    normalized=normalizer.normalize_reddit(raw_data=reddit_data,processed_data=processed_reddit)
    normalized.extend(normalizer.normalize_youtube(raw_data=yt_data,processed_data=processed_yt))
    normalized.extend(normalizer.normalize_google_trends(raw_data=trends_data,processed_data=processed_trends))

    new_dir=(BASE_DIR.parent.parent/"data"/"normalised")
    new_dir.mkdir(parents=True, exist_ok=True)

    with open(f"{new_dir}/normalised.json","w",encoding="utf-8") as f:
        json.dump(normalized,f,indent=4)