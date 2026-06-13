import json
from pathlib import Path
from time import sleep
from datetime import datetime, UTC
import pandas as pd
import shutil
from selenium.webdriver.common.by import By
from Fallback.scraper import build_driver
import hashlib


class GoogleTrendsCollector:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.temp_dir = (self.base_dir.parent.parent/ "data"/ "temp")
        self.temp_dir.mkdir(parents=True,exist_ok=True)

    def save(self, data):
        raw_dir = (self.base_dir.parent.parent/ "data"/ "raw")
        raw_dir.mkdir(parents=True,exist_ok=True)
        filename = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S-google-trends.json")

        filepath = raw_dir / filename

        with open(filepath,"w",encoding="utf-8") as f:
            json.dump(data,f,indent=4,ensure_ascii=False)
    
    @staticmethod
    def parse_search_volume(value):
        if pd.isna(value) or value == "":
            return ""
        value = str(value).strip().upper().replace("+", "")

        multipliers = {
            "K": 1_000,
            "M": 1_000_000,
            "B": 1_000_000_000,
        }
        suffix = value[-1]

        if suffix in multipliers:
            try:
                return int(float(value[:-1]) * multipliers[suffix])
            except ValueError:
                return value
        try:
            return int(value)
        except ValueError:
            return value
        
    @staticmethod
    def parse_datetime(value):
        if pd.isna(value) or value == "":
            return ""
        try:
            dt = datetime.strptime(value,"%B %d, %Y at %I:%M:%S %p UTC%z")
            return dt.strftime("%Y-%m-%d_%H.%M.%S")
        except Exception:
            return value
        
    @staticmethod
    def generate_id(row):
        seed = (f"{row.get('Trends', '')}|"f"{row.get('Started', '')}|")
        return hashlib.sha256(
            seed.encode("utf-8")
        ).hexdigest()

    def collect(self,region="IN"):
        driver = build_driver(download_dir=str(self.temp_dir))
        extraction_time = datetime.now(UTC).strftime("%Y-%m-%d_%H.%M.%S")

        try:
            driver.get(f"https://trends.google.com/trending?geo={region}")
            sleep(10)

            export_buttons = driver.find_elements(By.CSS_SELECTOR,'button[aria-label="Export"]')
            export_button = export_buttons[0]
            driver.execute_script(
                "arguments[0].click();",
                export_button
            )
            sleep(2)

            csv_buttons = driver.find_elements(By.CSS_SELECTOR,'li[data-action="csv"]')

            if not csv_buttons:
                raise RuntimeError("Could not find Download CSV menu item.")

            driver.execute_script("arguments[0].click();",csv_buttons[0])
            sleep(10)

            csv_files = sorted(
                self.temp_dir.glob("*.csv"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            if not csv_files:
                raise RuntimeError("No CSV file found in temp directory.")

            csv_path = csv_files[0]

            df = pd.read_csv(csv_path)
            df = df.where(pd.notna(df), "")

            if "Search volume" in df.columns:
                df["Search volume"] = df["Search volume"].apply(self.parse_search_volume)

            if "Started" in df.columns:
                df["Started"] = df["Started"].apply(self.parse_datetime)

            if "Ended" in df.columns:
                df["Ended"] = df["Ended"].apply(self.parse_datetime)

            df["region"] = region
            df["source"] = "google_trends"
            df["extraction_time"] = extraction_time
            df.insert(0,"id",df.apply(self.generate_id,axis=1))
            data = df.to_dict(orient="records")
            shutil.rmtree(self.temp_dir,ignore_errors=True)
            self.save(data)
            return data
        
        finally:
            driver.quit()

if __name__ == "__main__":
    collector = GoogleTrendsCollector()

    try:
        data = collector.collect()

    except Exception as e:
        raise