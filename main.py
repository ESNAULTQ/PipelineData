import uvicorn
import pandas as pd
from pymongo import MongoClient
from src.routes.app import app
from src.database import engine
from src.models.models import YellowTaxiTrip, ImportLog
from sqlmodel import SQLModel
import os

class DataCleaner:
    """Classe pour nettoyer les données en chunks"""
    
    def __init__(self):
        self.chunk_size = 100000
        self.offset = 0
    
    def clean_and_save_data(self):
        """Nettoie et sauvegarde les données chunk par chunk"""
        print("Début du nettoyage et sauvegarde des données...")
        
        # Configuration MongoDB
        user = os.getenv('MONGO_USER')
        password = os.getenv('MONGO_PASSWORD')
        host = os.getenv('MONGO_HOST')
        port = os.getenv('MONGO_PORT')
        
        client = MongoClient(f"mongodb://{user}:{password}@{host}:{port}/")
        db = client['taxi_data']
        collection = db['cleaned_trips']
        
        total_processed = 0
        
        while True:
            query = f"""
                SELECT vendorid, tpep_pickup_datetime, tpep_dropoff_datetime, passenger_count, trip_distance, ratecodeid, store_and_fwd_flag, pulocationid, dolocationid, payment_type, fare_amount, extra, mta_tax, tip_amount, tolls_amount, improvement_surcharge, total_amount, congestion_surcharge, airport_fee, cbd_congestion_fee
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
            
            # Convertir le chunk en liste de dictionnaires
            chunk_data = chunk_df.to_dict('records')
            
            # Insérer le chunk dans MongoDB
            if chunk_data:
                collection.insert_many(chunk_data)
                total_processed += len(chunk_data)
                print(f"✅ Chunk sauvegardé: {len(chunk_data)} enregistrements (Total: {total_processed})")
            
            self.offset += self.chunk_size
        
        print(f"✅ Traitement terminé! Total: {total_processed} enregistrements sauvegardés dans MongoDB")
        client.close()
        return total_processed
    
    
    def close(self):
        """Ferme les connexions et nettoie les ressources"""
        print("Fermeture du DataCleaner...")
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
    
    # Nettoyer et sauvegarder les données chunk par chunk
    cleaner = DataCleaner()
    try:
        # Nettoyer et sauvegarder en une seule opération
        total_processed = cleaner.clean_and_save_data()
        print(f"🎉 Traitement terminé avec succès! {total_processed} enregistrements traités.")
    finally:
        cleaner.close()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
