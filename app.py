from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from typing import List, Optional
from datetime import datetime
import uvicorn

from src.database import engine, get_session
from src.models.models import YellowTaxiTrip, ImportLog
from src.crud.crud import YellowTaxiTripCRUD, ImportLogCRUD

# Créer l'application FastAPI
app = FastAPI(
    title="NYC Taxi Data Pipeline API",
    description="API pour analyser les données des taxis jaunes de NYC",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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

# ==================== ROUTES POUR YELLOW TAXI TRIPS ====================

@app.get("/trips", response_model=List[YellowTaxiTrip])
async def get_all_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Récupérer tous les voyages avec pagination"""
    return YellowTaxiTripCRUD.get_all_trips(db, skip=skip, limit=limit)

@app.get("/trips/{trip_id}", response_model=YellowTaxiTrip)
async def get_trip_by_id(trip_id: int, db: Session = Depends(get_db)):
    """Récupérer un voyage par son ID"""
    trip = YellowTaxiTripCRUD.get_trip_by_id(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")
    return trip

@app.post("/trips", response_model=YellowTaxiTrip)
async def create_trip(trip_data: dict, db: Session = Depends(get_db)):
    """Créer un nouveau voyage"""
    return YellowTaxiTripCRUD.create_trip(db, trip_data)

@app.put("/trips/{trip_id}", response_model=YellowTaxiTrip)
async def update_trip(trip_id: int, trip_data: dict, db: Session = Depends(get_db)):
    """Mettre à jour un voyage"""
    trip = YellowTaxiTripCRUD.update_trip(db, trip_id, trip_data)
    if not trip:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")
    return trip

@app.delete("/trips/{trip_id}")
async def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    """Supprimer un voyage"""
    success = YellowTaxiTripCRUD.delete_trip(db, trip_id)
    if not success:
        raise HTTPException(status_code=404, detail="Voyage non trouvé")
    return {"message": "Voyage supprimé avec succès"}

@app.get("/trips/by-date-range")
async def get_trips_by_date_range(
    start_date: datetime = Query(..., description="Date de début (YYYY-MM-DDTHH:MM:SS)"),
    end_date: datetime = Query(..., description="Date de fin (YYYY-MM-DDTHH:MM:SS)"),
    db: Session = Depends(get_db)
):
    """Récupérer les voyages dans une plage de dates"""
    return YellowTaxiTripCRUD.get_trips_by_date_range(db, start_date, end_date)

@app.get("/trips/by-location")
async def get_trips_by_location(
    pickup_location: int = Query(..., description="ID de la zone de prise en charge"),
    dropoff_location: Optional[int] = Query(None, description="ID de la zone de dépose"),
    db: Session = Depends(get_db)
):
    """Récupérer les voyages par localisation"""
    return YellowTaxiTripCRUD.get_trips_by_location(db, pickup_location, dropoff_location)

@app.get("/trips/by-payment-type/{payment_type}")
async def get_trips_by_payment_type(payment_type: int, db: Session = Depends(get_db)):
    """Récupérer les voyages par type de paiement"""
    return YellowTaxiTripCRUD.get_trips_by_payment_type(db, payment_type)

@app.get("/trips/by-distance-range")
async def get_trips_by_distance_range(
    min_distance: float = Query(..., ge=0),
    max_distance: float = Query(..., ge=0),
    db: Session = Depends(get_db)
):
    """Récupérer les voyages par distance"""
    return YellowTaxiTripCRUD.get_trips_by_distance_range(db, min_distance, max_distance)

@app.get("/trips/by-fare-range")
async def get_trips_by_fare_range(
    min_fare: float = Query(..., ge=0),
    max_fare: float = Query(..., ge=0),
    db: Session = Depends(get_db)
):
    """Récupérer les voyages par montant de course"""
    return YellowTaxiTripCRUD.get_trips_by_fare_range(db, min_fare, max_fare)

@app.get("/trips/with-passengers")
async def get_trips_with_passengers(
    min_passengers: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    """Récupérer les voyages avec passagers"""
    return YellowTaxiTripCRUD.get_trips_with_passengers(db, min_passengers)

@app.get("/trips/statistics")
async def get_trip_statistics(db: Session = Depends(get_db)):
    """Récupérer les statistiques générales des voyages"""
    return YellowTaxiTripCRUD.get_statistics(db)

@app.get("/trips/top-pickup-locations")
async def get_top_pickup_locations(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Récupérer les principales zones de prise en charge"""
    return YellowTaxiTripCRUD.get_top_pickup_locations(db, limit)

@app.get("/trips/top-dropoff-locations")
async def get_top_dropoff_locations(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Récupérer les principales zones de dépose"""
    return YellowTaxiTripCRUD.get_top_dropoff_locations(db, limit)

# ==================== ROUTES POUR IMPORT LOGS ====================

@app.get("/import-logs", response_model=List[ImportLog])
async def get_all_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Récupérer tous les logs d'importation avec pagination"""
    return ImportLogCRUD.get_all_logs(db, skip=skip, limit=limit)

@app.get("/import-logs/{file_name}", response_model=ImportLog)
async def get_log_by_filename(file_name: str, db: Session = Depends(get_db)):
    """Récupérer un log par nom de fichier"""
    log = ImportLogCRUD.get_log_by_filename(db, file_name)
    if not log:
        raise HTTPException(status_code=404, detail="Log non trouvé")
    return log

@app.post("/import-logs", response_model=ImportLog)
async def create_log(
    file_name: str,
    status: str,
    db: Session = Depends(get_db)
):
    """Créer un nouveau log d'importation"""
    return ImportLogCRUD.create_log(db, file_name, status)

@app.put("/import-logs/{file_name}", response_model=ImportLog)
async def update_log_status(
    file_name: str,
    status: str,
    db: Session = Depends(get_db)
):
    """Mettre à jour le statut d'un log"""
    log = ImportLogCRUD.update_log_status(db, file_name, status)
    if not log:
        raise HTTPException(status_code=404, detail="Log non trouvé")
    return log

@app.delete("/import-logs/{file_name}")
async def delete_log(file_name: str, db: Session = Depends(get_db)):
    """Supprimer un log"""
    success = ImportLogCRUD.delete_log(db, file_name)
    if not success:
        raise HTTPException(status_code=404, detail="Log non trouvé")
    return {"message": "Log supprimé avec succès"}

@app.get("/import-logs/by-status/{status}")
async def get_logs_by_status(status: str, db: Session = Depends(get_db)):
    """Récupérer les logs par statut"""
    return ImportLogCRUD.get_logs_by_status(db, status)

@app.get("/import-logs/by-date-range")
async def get_logs_by_date_range(
    start_date: datetime = Query(..., description="Date de début (YYYY-MM-DDTHH:MM:SS)"),
    end_date: datetime = Query(..., description="Date de fin (YYYY-MM-DDTHH:MM:SS)"),
    db: Session = Depends(get_db)
):
    """Récupérer les logs dans une plage de dates"""
    return ImportLogCRUD.get_logs_by_date_range(db, start_date, end_date)

@app.get("/import-logs/recent")
async def get_recent_logs(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Récupérer les logs récents"""
    return ImportLogCRUD.get_recent_logs(db, limit)

# ==================== ROUTES DE SANTÉ ====================

@app.get("/health")
async def health_check():
    """Vérifier l'état de l'API"""
    return {"status": "healthy", "message": "API fonctionne correctement"}

@app.get("/")
async def root():
    """Page d'accueil avec liens vers la documentation"""
    return {
        "message": "NYC Taxi Data Pipeline API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
