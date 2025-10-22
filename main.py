import uvicorn
import pandas as pd
from src.routes.app import app
from src.database import engine
from src.models.models import YellowTaxiTrip, ImportLog
from sqlmodel import SQLModel

class DataCleaner:
    """Classe pour nettoyer les données en chunks"""
    
    def __init__(self):
        self.chunk_size = 100000
        self.offset = 0
        self.cleaned_data = pd.DataFrame()
    
    def clean_data(self, df):
        """Nettoie les données en chunks"""
        print("Début du nettoyage des données...")
        
        while True:
            query = f"""
                SELECT * 
                FROM yellowtaxitrip
                WHERE (passenger_count >= 0 OR trip_distance >= 0 OR fare_amount >= 0 OR tip_amount >= 0 OR tolls_amount >= 0 OR total_amount >= 0)
                AND passenger_count BETWEEN 1 and 8
                AND trip_distance <= 100
                AND fare_amount <= 500
                AND tpep_pickup_datetime IS NOT NULL
                AND tpep_dropoff_datetime IS NOT NULL
                LIMIT {self.chunk_size} OFFSET {self.offset}
            """
            
            chunk_df = pd.read_sql(query, engine)
            
            if chunk_df.empty:
                break
            
            self.cleaned_data = pd.concat([self.cleaned_data, chunk_df], ignore_index=True)
            self.offset += self.chunk_size
            print(f"Processed {self.offset} rows...")
        
        print(f"Total rows processed: {len(self.cleaned_data)}")
        return self.cleaned_data
    
    def close(self):
        """Ferme les connexions et nettoie les ressources"""
        print("Fermeture du DataCleaner...")
        self.cleaned_data = pd.DataFrame()
        self.offset = 0

def init_database():
    """Initialiser la base de données au démarrage"""
    try:
        print("Initialisation de la base de données...")
        SQLModel.metadata.create_all(engine)
        print("✅ Base de données initialisée avec succès!")
        
        # Vérifier les tables créées
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables disponibles: {tables}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
        # Ne pas faire échouer le démarrage, juste afficher l'erreur
        

if __name__ == "__main__":
    # Initialiser la base de données au démarrage
    init_database()
    
    # Nettoyer les données
    cleaner = DataCleaner()
    try:
        # Nettoyer
        cleaned_df = cleaner.clean_data(df)
    finally:
        cleaner.close()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
