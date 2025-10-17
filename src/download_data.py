from pathlib import Path
import requests
import datetime

class NYCTaxiDataDownloader:
    def __init__(self, year: int, month: int):
        self.BASE_URL = "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"
        self.YEAR=2025
        self.DATA_DIR= "data/raw"
    
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
                url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{self.YEAR}-{month:02d}.parquet"
                
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                # Créer le répertoire s'il n'existe pas
                file_path = self.get_file_path(month)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Sauvegarder le fichier
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"File for month {month} downloaded successfully to {file_path}")
                return True

        except requests.exceptions.RequestException as e:
            print(f"Error downloading file for month {month}: {e}")
            return False
    
    def download_all_available(self) -> bool :
        month_actuel = datetime.datetime.now().month
        for month in range(1, month_actuel - 1):
            if self.download_month(month):
                pass
            else:
                print(f"Error downloading file for month {month}")
        return True

nyt = NYCTaxiDataDownloader(2025, 1)
nyt.download_all_available()
print("Pipeline de données NYC Taxi initialisé")