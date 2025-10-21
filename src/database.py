import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text

# Configuration de la base de données PostgreSQL
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')

# Créer l'URL de connexion SQLModel
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Créer le moteur SQLModel
engine = create_engine(DATABASE_URL, echo=True)

# Fonction pour créer une session de base de données
def get_session():
    """Créer une nouvelle session de base de données"""
    return Session(engine) 