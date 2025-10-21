from fastapi import FastAPI, Depends, HTTPException, Query, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from typing import List, Optional
from datetime import datetime
import uvicorn
import asyncio
import subprocess
import sys
import os
from pathlib import Path

from ..database import engine, get_session
from ..models.models import YellowTaxiTrip, ImportLog, TaxiTripCreate, TaxiTripUpdate, Statistics
from ..crud.crud import TaxiTripService, ImportLogCRUD
from sqlmodel import SQLModel

# Créer l'application FastAPI
app = FastAPI(
    title="NYC Taxi Data Pipeline API",
    description="API pour analyser les données des taxis jaunes de NYC",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Créer un routeur pour l'API v1
api_v1 = APIRouter(prefix="/api/v1", tags=["API v1"])

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency pour obtenir une session de base de données
def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()

# ==================== ROUTES POUR TAXI TRIPS (API v1) ====================

@api_v1.get("/trips", response_model=List[YellowTaxiTrip])
async def get_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Récupérer une liste de trajets avec pagination"""
    trips, total = TaxiTripService.get_trips(db, skip, limit)
    return trips

@api_v1.get("/trips/{trip_id}", response_model=YellowTaxiTrip)
async def get_trip(trip_id: int, db: Session = Depends(get_db)):
    """Récupérer un trajet par ID"""
    trip = TaxiTripService.get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trajet non trouvé")
    return trip

@api_v1.post("/trips", response_model=YellowTaxiTrip)
async def create_trip(trip: TaxiTripCreate, db: Session = Depends(get_db)):
    """Créer un nouveau trajet"""
    return TaxiTripService.create_trip(db, trip)

@api_v1.put("/trips/{trip_id}", response_model=YellowTaxiTrip)
async def update_trip(trip_id: int, trip: TaxiTripUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un trajet existant"""
    updated_trip = TaxiTripService.update_trip(db, trip_id, trip)
    if not updated_trip:
        raise HTTPException(status_code=404, detail="Trajet non trouvé")
    return updated_trip

@api_v1.delete("/trips/{trip_id}")
async def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    """Supprimer un trajet"""
    success = TaxiTripService.delete_trip(db, trip_id)
    if not success:
        raise HTTPException(status_code=404, detail="Trajet non trouvé")
    return {"message": "Trajet supprimé avec succès"}

@api_v1.get("/statistics", response_model=Statistics)
async def get_statistics(db: Session = Depends(get_db)):
    """Récupérer les statistiques des trajets"""
    return TaxiTripService.get_statistics(db)


# ==================== ROUTES POUR PIPELINE DE DONNÉES (API v1) ====================

@api_v1.post("/pipeline/run")
async def run_pipeline():
    """Exécuter le pipeline complet : téléchargement puis importation"""
    try:
        # Étape 1: Téléchargement
        script_path = Path("src/download_data.py")
        if not script_path.exists():
            raise HTTPException(status_code=404, detail="Script download_data.py non trouvé")
        
        # Exécuter le script de téléchargement
        process = subprocess.Popen([
            sys.executable, str(script_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        stdout, stderr = process.communicate(timeout=300)  # 5 minutes timeout
        
        if process.returncode != 0:
            return {
                "status": "error",
                "message": "Erreur lors du téléchargement des données",
                "error": stderr,
                "output": stdout
            }
        
        # Étape 2: Importation
        script_path = Path("src/import_data_postgres.py")
        if not script_path.exists():
            raise HTTPException(status_code=404, detail="Script import_data_postgres.py non trouvé")
        
        # Exécuter le script d'importation
        process = subprocess.Popen([
            sys.executable, str(script_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        stdout, stderr = process.communicate(timeout=1800)  # 30 minutes timeout
        
        if process.returncode == 0:
            return {
                "status": "success",
                "message": "Pipeline exécuté avec succès",
                "output": stdout
            }
        else:
            return {
                "status": "error",
                "message": "Erreur lors de l'importation des données",
                "error": stderr,
                "output": stdout
            }
            
    except subprocess.TimeoutExpired:
        process.kill()
        raise HTTPException(status_code=408, detail="Timeout lors de l'exécution du pipeline")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'exécution du pipeline: {str(e)}")

# ==================== ENREGISTREMENT DU ROUTEUR API v1 ====================

# Enregistrer le routeur API v1 avec l'application principale
app.include_router(api_v1)

# ==================== ROUTES DE GESTION DE BASE DE DONNÉES ====================

@app.post("/db/init")
async def init_database():
    """Initialiser la base de données en créant toutes les tables"""
    try:
        SQLModel.metadata.create_all(engine)
        
        # Vérifier les tables créées
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        return {
            "status": "success",
            "message": "Base de données initialisée avec succès",
            "tables_created": tables
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'initialisation de la base de données: {str(e)}")

@app.get("/db/tables")
async def get_database_tables():
    """Lister toutes les tables de la base de données"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        return {
            "status": "success",
            "tables": tables,
            "count": len(tables)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des tables: {str(e)}")

@app.post("/db/drop")
async def drop_database_tables():
    """Supprimer toutes les tables de la base de données (ATTENTION: destructif!)"""
    try:
        SQLModel.metadata.drop_all(engine)
        return {
            "status": "success",
            "message": "Toutes les tables ont été supprimées"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression des tables: {str(e)}")

# ==================== ROUTES DE SANTÉ ====================

@app.get("/health")
async def health_check():
    """Vérifier l'état de l'API"""
    return {"status": "healthy", "message": "API fonctionne correctement"}

@app.get("/")
async def root():
    """Page d'accueil avec informations sur l'API"""
    return {
        "message": "NYC Taxi Data Pipeline API",
        "version": "1.0.0",
        "description": "API pour analyser les données des taxis jaunes de NYC",
        "endpoints": {
            "info": "GET /",
            "health": "GET /health",
            "trips": {
                "list": "GET /api/v1/trips",
                "get": "GET /api/v1/trips/{id}",
                "create": "POST /api/v1/trips",
                "update": "PUT /api/v1/trips/{id}",
                "delete": "DELETE /api/v1/trips/{id}"
            },
            "statistics": "GET /api/v1/statistics",
            "pipeline": "POST /api/v1/pipeline/run"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }
