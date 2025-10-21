import uvicorn
from src.routes.app import app
from src.database import engine
from src.models.models import YellowTaxiTrip, ImportLog
from sqlmodel import SQLModel

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
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
