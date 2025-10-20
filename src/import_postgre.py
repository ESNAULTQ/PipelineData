import pandas as pd
from pathlib import Path
import datetime
import logging
import os
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NYCTaxiDataImporterPostgres:
    def __init__(self):
        self.DATA_DIR = "data/raw"
        
        # Configuration de la base de données PostgreSQL
        self.POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
        self.POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')
        self.POSTGRES_DB = os.getenv('POSTGRES_DB', 'nyc_taxi')
        self.POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
        self.POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
        
        # Créer l'URL de connexion SQLAlchemy
        self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
        # Initialiser la connexion
        self.engine = self._init_database()

    def _init_database(self):
        """Initialize PostgreSQL connection and create necessary tables"""
        engine = create_engine(self.DATABASE_URL)
        
        # Créer la table de log d'import si elle n'existe pas
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS import_log (
                    file_name VARCHAR(255) PRIMARY KEY,
                    import_date TIMESTAMP NOT NULL,
                    status VARCHAR(50) NOT NULL
                )
            """))
            
            # Créer la table principale des données de taxi si elle n'existe pas
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS yellow_taxi_trips (
                    VendorID INTEGER,
                    tpep_pickup_datetime TIMESTAMP,
                    tpep_dropoff_datetime TIMESTAMP,
                    passenger_count DOUBLE PRECISION,
                    trip_distance DOUBLE PRECISION,
                    RatecodeID DOUBLE PRECISION,
                    store_and_fwd_flag VARCHAR(1),
                    PULocationID INTEGER,
                    DOLocationID INTEGER,
                    payment_type INTEGER,
                    fare_amount DOUBLE PRECISION,
                    extra DOUBLE PRECISION,
                    mta_tax DOUBLE PRECISION,
                    tip_amount DOUBLE PRECISION,
                    tolls_amount DOUBLE PRECISION,
                    improvement_surcharge DOUBLE PRECISION,
                    total_amount DOUBLE PRECISION,
                    congestion_surcharge DOUBLE PRECISION,
                    airport_fee DOUBLE PRECISION,
                    cbd_congestion_fee DOUBLE PRECISION
                )
            """))
            conn.commit()
        
        return engine

    def _is_file_imported(self, file_name: str) -> bool:
        """Check if file has already been imported successfully"""
        with self.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT status FROM import_log WHERE file_name = :file_name"
            ), {"file_name": file_name}).fetchone()
            
            return result is not None and result[0] == 'success'

    def import_file(self, file_path: Path) -> bool:
        """Import a single Parquet file into PostgreSQL"""
        file_name = file_path.name
        
        if self._is_file_imported(file_name):
            logger.info(f"File {file_name} already imported, skipping")
            return True

        try:
            # Lire le fichier Parquet avec pandas
            df = pd.read_parquet(file_path)
            
            # Importer les données dans PostgreSQL
            df.to_sql(
                'yellow_taxi_trips', 
                self.engine, 
                if_exists='append', 
                index=False
            )

            # Enregistrer l'import réussi
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO import_log (file_name, import_date, status)
                    VALUES (:file_name, :import_date, :status)
                    ON CONFLICT (file_name) DO UPDATE 
                    SET import_date = excluded.import_date, status = excluded.status
                """), {
                    "file_name": file_name, 
                    "import_date": datetime.datetime.now(), 
                    "status": 'success'
                })
                conn.commit()

            logger.info(f"Successfully imported {file_name}")
            return True

        except Exception as e:
            logger.error(f"Error importing {file_name}: {e}")
            
            # Enregistrer l'échec d'import
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO import_log (file_name, import_date, status)
                    VALUES (:file_name, :import_date, :status)
                    ON CONFLICT (file_name) DO UPDATE 
                    SET import_date = excluded.import_date, status = excluded.status
                """), {
                    "file_name": file_name, 
                    "import_date": datetime.datetime.now(), 
                    "status": 'failed'
                })
                conn.commit()
            
            return False

    def import_all_files(self) -> bool:
        """Import all Parquet files from the data directory"""
        success = True
        data_dir = Path(self.DATA_DIR)
        
        for file_path in data_dir.glob("*.parquet"):
            if not self.import_file(file_path):
                success = False

        return success

if __name__ == "__main__":
    importer = NYCTaxiDataImporterPostgres()
    importer.import_all_files()
