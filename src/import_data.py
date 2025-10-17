import duckdb
from pathlib import Path
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NYCTaxiDataImporter:
    def __init__(self):
        self.DATA_DIR = "data/raw"
        self.DB_PATH = "data/nyc_taxi.duckdb"
        self.db = self._init_database()

    def _init_database(self) -> duckdb.DuckDBPyConnection:
        """Initialize DuckDB connection and create necessary tables"""
        db = duckdb.connect(self.DB_PATH)
        
        # Create import log table if it doesn't exist
        db.execute("""
            CREATE TABLE IF NOT EXISTS import_log (
                file_name VARCHAR,
                import_date TIMESTAMP,
                status VARCHAR,
                PRIMARY KEY (file_name)
            )
        """)
        
        # Create main taxi data table if it doesn't exist
        db.execute("""
            CREATE TABLE IF NOT EXISTS yellow_taxi_trips (
                VendorID INTEGER,
                tpep_pickup_datetime TIMESTAMP,
                tpep_dropoff_datetime TIMESTAMP,
                passenger_count DOUBLE,
                trip_distance DOUBLE,
                RatecodeID DOUBLE,
                store_and_fwd_flag VARCHAR,
                PULocationID INTEGER,
                DOLocationID INTEGER,
                payment_type INTEGER,
                fare_amount DOUBLE,
                extra DOUBLE,
                mta_tax DOUBLE,
                tip_amount DOUBLE,
                tolls_amount DOUBLE,
                improvement_surcharge DOUBLE,
                total_amount DOUBLE,
                congestion_surcharge DOUBLE,
                airport_fee DOUBLE,
                cbd_congestion_fee DOUBLE
            )
        """)
        return db

    def _is_file_imported(self, file_name: str) -> bool:
        """Check if file has already been imported successfully"""
        result = self.db.execute(
            "SELECT status FROM import_log WHERE file_name = ?",
            [file_name]
        ).fetchone()
        return result is not None and result[0] == 'success'

    def import_file(self, file_path: Path) -> bool:
        """Import a single Parquet file into DuckDB"""
        file_name = file_path.name
        
        if self._is_file_imported(file_name):
            logger.info(f"File {file_name} already imported, skipping")
            return True

        try:
            # Import Parquet file into taxi data table
            self.db.execute("""
                INSERT INTO yellow_taxi_trips 
                SELECT * FROM read_parquet(?)
            """, [str(file_path)])

            # Log successful import
            self.db.execute("""
                INSERT INTO import_log (file_name, import_date, status)
                VALUES (?, ?, ?)
                ON CONFLICT (file_name) DO UPDATE 
                SET import_date = excluded.import_date, status = excluded.status
            """, [file_name, datetime.datetime.now(), 'success'])

            logger.info(f"Successfully imported {file_name}")
            return True

        except Exception as e:
            logger.error(f"Error importing {file_name}: {e}")
            
            # Log failed import
            self.db.execute("""
                INSERT INTO import_log (file_name, import_date, status)
                VALUES (?, ?, ?)
                ON CONFLICT (file_name) DO UPDATE 
                SET import_date = excluded.import_date, status = excluded.status
            """, [file_name, datetime.datetime.now(), 'failed'])
            
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
    importer = NYCTaxiDataImporter()
    importer.import_all_files()
