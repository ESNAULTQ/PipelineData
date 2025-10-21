import pandas as pd
from pathlib import Path
import datetime
import logging
import os
from sqlalchemy import create_engine, text
import psycopg2
import pyarrow.parquet as pq
import pyarrow.dataset as ds

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NYCTaxiDataImporterPostgres:
    def __init__(self):
        self.DATA_DIR = "data/raw"
        # Paramètres de streaming ajustables via env
        self.PARQUET_BATCH_SIZE = int(os.getenv('PARQUET_BATCH_SIZE', '100000'))  # lignes par batch PyArrow
        self.SQL_CHUNK_SIZE = int(os.getenv('SQL_CHUNK_SIZE', '100000'))          # lignes par insert pandas
        
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
        try:
            engine = create_engine(self.DATABASE_URL)
            
            # Tester la connexion
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Créer les tables si elles n'existent pas
            self._create_tables(engine)
            
            logger.info("Connexion à PostgreSQL établie avec succès")
            return engine
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à PostgreSQL: {e}")
            raise

    def _create_tables(self, engine):
        """Create necessary tables in PostgreSQL"""
        with engine.connect() as conn:
            # Créer la table de log d'import si elle n'existe pas
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS importlog (
                    file_name VARCHAR(255) PRIMARY KEY,
                    import_date TIMESTAMP NOT NULL,
                    status VARCHAR(50) NOT NULL
                )
            """))
            
            # Recréer la table principale avec un schéma robuste (id auto et noms en minuscules)
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS yellowtaxitrip (
                id SERIAL PRIMARY KEY,
                vendorid INTEGER,
                tpep_pickup_datetime TIMESTAMP,
                tpep_dropoff_datetime TIMESTAMP,
                passenger_count DOUBLE PRECISION,
                trip_distance DOUBLE PRECISION,
                ratecodeid DOUBLE PRECISION,
                store_and_fwd_flag VARCHAR(1),
                pulocationid INTEGER,
                dolocationid INTEGER,
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

    def _is_file_imported(self, file_name: str) -> bool:
        """Check if file has already been imported successfully"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT status FROM importlog WHERE file_name = :file_name"
                ), {"file_name": file_name}).fetchone()
                
                return result is not None and result[0] == 'success'
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du fichier {file_name}: {e}")
            return False

    def import_file(self, file_path: Path) -> bool:
        """Import d'un fichier Parquet vers PostgreSQL en streaming (faible mémoire)"""
        file_name = file_path.name
        
        if self._is_file_imported(file_name):
            logger.info(f"Fichier {file_name} déjà importé, ignoré")
            return True

        try:
            logger.info(f"Lecture en flux du fichier {file_name} (batch={self.PARQUET_BATCH_SIZE})")

            # Utiliser PyArrow pour itérer par batches sans charger tout le fichier
            parquet_file = pq.ParquetFile(str(file_path))
            total_rows = parquet_file.metadata.num_rows if parquet_file.metadata is not None else None
            processed_rows = 0

            for batch in parquet_file.iter_batches(batch_size=self.PARQUET_BATCH_SIZE):
                # Conversion en DataFrame pandas par batch
                df_batch = batch.to_pandas(types_mapper=self._arrow_types_mapper)

                # Nettoyage léger sur le batch
                df_batch = self._clean_data(df_batch)

                # Écriture par morceaux pour limiter la mémoire et la taille des requêtes
                df_batch.to_sql(
                    'yellowtaxitrip',
                    self.engine,
                    if_exists='append',
                    index=False,
                    method='multi',
                    chunksize=self.SQL_CHUNK_SIZE
                )

                processed_rows += len(df_batch)
                if total_rows is not None:
                    logger.info(f"Progression {file_name}: {processed_rows}/{total_rows} lignes")
                else:
                    logger.info(f"Progression {file_name}: {processed_rows} lignes traitées")

            # Enregistrer l'import réussi
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO importlog (file_name, import_date, status)
                    VALUES (:file_name, :import_date, :status)
                    ON CONFLICT (file_name) DO UPDATE 
                    SET import_date = excluded.import_date, status = excluded.status
                """), {
                    "file_name": file_name, 
                    "import_date": datetime.datetime.now(), 
                    "status": 'success'
                })
                conn.commit()

            logger.info(f"Import réussi de {file_name}")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'import de {file_name}: {e}")
            
            # Enregistrer l'échec d'import
            try:
                with self.engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO importlog (file_name, import_date, status)
                        VALUES (:file_name, :import_date, :status)
                        ON CONFLICT (file_name) DO UPDATE 
                        SET import_date = excluded.import_date, status = excluded.status
                    """), {
                        "file_name": file_name, 
                        "import_date": datetime.datetime.now(), 
                        "status": 'failed'
                    })
                    conn.commit()
            except Exception as log_error:
                logger.error(f"Erreur lors de l'enregistrement de l'échec: {log_error}")
            
            return False

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Nettoie et harmonise les colonnes pour correspondre au schéma SQL (minuscules)."""
        # Uniformiser les noms de colonnes en minuscules
        df.columns = [str(c).lower() for c in df.columns]

        # Harmoniser quelques variantes connues
        rename_map = {
            'airport_fee$': 'airport_fee',
        }
        df = df.rename(columns=rename_map)

        # Colonnes attendues par la table cible (ordre contrôlé)
        allowed_columns = [
            'vendorid',
            'tpep_pickup_datetime',
            'tpep_dropoff_datetime',
            'passenger_count',
            'trip_distance',
            'ratecodeid',
            'store_and_fwd_flag',
            'pulocationid',
            'dolocationid',
            'payment_type',
            'fare_amount',
            'extra',
            'mta_tax',
            'tip_amount',
            'tolls_amount',
            'improvement_surcharge',
            'total_amount',
            'congestion_surcharge',
            'airport_fee',
            'cbd_congestion_fee',
        ]
        existing_columns = [c for c in allowed_columns if c in df.columns]
        df = df[existing_columns]

        # Supprimer les lignes avec des valeurs nulles dans les colonnes critiques
        critical_columns = [c for c in ['tpep_pickup_datetime', 'tpep_dropoff_datetime'] if c in df.columns]
        if critical_columns:
            df = df.dropna(subset=critical_columns)
        
        # Convertir les types de données si nécessaire
        for col in ['tpep_pickup_datetime', 'tpep_dropoff_datetime']:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                except Exception as e:
                    logger.warning(f"Erreur lors de la conversion de {col}: {e}")
        
        return df

    @staticmethod
    def _arrow_types_mapper(pa_type):
        """Mapper optionnel des types Arrow vers pandas pour une meilleure compatibilité."""
        # Laisser pandas décider par défaut; ce hook existe pour étendre si besoin.
        return None

    def import_all_files(self) -> bool:
        """Import all Parquet files from the data directory"""
        success = True
        data_dir = Path(self.DATA_DIR)
        
        if not data_dir.exists():
            logger.error(f"Le répertoire {self.DATA_DIR} n'existe pas")
            return False
        
        parquet_files = list(data_dir.glob("*.parquet"))
        if not parquet_files:
            logger.warning(f"Aucun fichier Parquet trouvé dans {self.DATA_DIR}")
            return True
        
        logger.info(f"Trouvé {len(parquet_files)} fichiers Parquet à importer")
        
        for file_path in parquet_files:
            logger.info(f"Traitement de {file_path.name}")
            if not self.import_file(file_path):
                success = False

        return success

    def get_import_stats(self):
        """Get import statistics"""
        try:
            with self.engine.connect() as conn:
                # Statistiques des imports
                import_stats = conn.execute(text("""
                    SELECT 
                        status,
                        COUNT(*) as count
                    FROM importlog 
                    GROUP BY status
                """)).fetchall()
                
                # Nombre total de voyages
                total_trips = conn.execute(text("""
                    SELECT COUNT(*) FROM yellowtaxitrip
                """)).fetchone()[0]
                
                logger.info("=== Statistiques d'import ===")
                for status, count in import_stats:
                    logger.info(f"Fichiers {status}: {count}")
                logger.info(f"Total des voyages importés: {total_trips}")
                
                return {
                    'import_stats': dict(import_stats),
                    'total_trips': total_trips
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return None

if __name__ == "__main__":
    importer = NYCTaxiDataImporterPostgres()
    
    # Importer tous les fichiers
    success = importer.import_all_files()
    
    if success:
        logger.info("Tous les fichiers ont été importés avec succès")
    else:
        logger.error("Certains fichiers n'ont pas pu être importés")
    
    # Afficher les statistiques
    importer.get_import_stats()
