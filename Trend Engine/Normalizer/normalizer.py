import json
from pathlib import Path
import hashlib

class Normalizer:
    def _generate_id(self,source,created_utc):
        text = (f"{source}|"f"{created_utc}")
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def normalize_reddit(self,processed_data):
        normalized = []
        for p in processed_data:
            normalized.append({
                "id": self._generate_id(
                    p["source"],
                    p["created_utc"],
                ),
                "source": p["source"],
                "region": p["region"],
                "created_utc": p["created_utc"],
                "extracted_utc": p["extracted_utc"],
                "tags": p["tags"],
                "concepts": p["concepts"],
                "keywords": p["keywords"],
                "interactions": [
                    p["upvotes"],
                    p["comments"]
                ]
            })

        return normalized

    def normalize_youtube(self,processed_data):
        normalized = []
        for p in processed_data:
            normalized.append({
                "id": self._generate_id(
                    p["source"],
                    p["published_at"],
                ),
                "source": p["source"],
                "region": p["region"],
                "created_utc": p["published_at"],
                "extracted_utc": p["extracted_utc"],
                "tags": p["tags"],
                "concepts": p["concepts"],
                "keywords": p["keywords"],
                "interactions": [
                    int(p["views"]),
                    int(p["likes"]),
                    int(p["comments"])
                ]
            })

        return normalized

    def normalize_google_trends(self,processed_data):
        normalized = []

        for p in processed_data:
            normalized.append({
                "id": self._generate_id(
                    p["source"],
                    p["Started"],
                ),
                "source": p["source"],
                "region": p["region"],
                "created_utc": p["Started"],
                "extracted_utc": p["extraction_utc"],
                "tags": p["tags"],
                "concepts": p["concepts"],
                "keywords": p["keywords"],
                "interactions": [
                    p["Search volume"]
                ]
            })

        return normalized

if __name__=="__main__":
    BASE_DIR = Path(__file__).resolve().parent
    dir=(BASE_DIR.parent.parent/"data"/"temp")

    with open(f"{dir}/reddit.json","r",encoding="utf-8") as f:
        reddit_data = json.load(f)


    with open(f"{dir}/youtube.json","r",encoding="utf-8") as f:
        yt_data = json.load(f)


    with open(f"{dir}/google-trends.json","r",encoding="utf-8") as f:
        trends_data=json.load(f)


    normalizer = Normalizer()
    normalized=normalizer.normalize_reddit(reddit_data)
    normalized.extend(normalizer.normalize_youtube(yt_data))
    normalized.extend(normalizer.normalize_google_trends(trends_data))

    new_dir=(BASE_DIR.parent.parent/"data"/"normalised")
    new_dir.mkdir(parents=True, exist_ok=True)

    with open(f"{new_dir}/normalised.json","w",encoding="utf-8") as f:
        json.dump(normalized,f,indent=4)