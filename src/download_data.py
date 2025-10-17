from pathlib import Path
import requests
import datetime

class NYCTaxiDataDownloader:
    def __init__(self, year: int, month: int):
        self.BASE_URL = "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"
        self.YEAR=2025
        self.DATA_DIR= "data\raw"
    
    def get_file_path(self, month: int) -> Path :
        return Path(self.DATA_DIR) / f"yellow_tripdata_{self.YEAR}-{month:02d}.parquet"

    def file_exists(self, month: int) -> bool:
        if self.get_file_path(month).exists():
            return True
        else:
            return False

    def download_month(self, month: int) -> bool :
        try:
            if self.file_exists(month):
                print(f"File for month {month} already exists")
                return True
            else:
                response = requests.get(f"{self.BASE_URL}/yellow_tripdata_{self.YEAR}-{month:02d}.parquet", stream=True, timeout=30)
                return response

        except requests.exceptions.RequestException as e:
            print(f"Error downloading file for month {month}: {e}")
            return False
    
    def download_all_available() -> list :
        month_actuel = datetime.datetime.now().month
        
