from sqlmodel import Session, select, func
from typing import List, Optional, Tuple
from datetime import datetime
from src.models.models import YellowTaxiTrip, ImportLog, TaxiTripCreate, TaxiTripUpdate, Statistics
from src.database import engine


class ImportLogCRUD:
    """CRUD operations for ImportLog model"""
    
    @staticmethod
    def create_log(session: Session, file_name: str, status: str) -> ImportLog:
        """Créer un nouveau log d'importation"""
        log = ImportLog(
            file_name=file_name,
            import_date=datetime.now(),
            status=status
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log
    
    @staticmethod
    def get_log_by_filename(session: Session, file_name: str) -> Optional[ImportLog]:
        """Récupérer un log par nom de fichier"""
        return session.get(ImportLog, file_name)
    
    @staticmethod
    def get_all_logs(session: Session, skip: int = 0, limit: int = 100) -> List[ImportLog]:
        """Récupérer tous les logs avec pagination"""
        statement = select(ImportLog).offset(skip).limit(limit)
        return session.exec(statement).all()
    
    @staticmethod
    def update_log_status(session: Session, file_name: str, status: str) -> Optional[ImportLog]:
        """Mettre à jour le statut d'un log"""
        log = session.get(ImportLog, file_name)
        if log:
            log.status = status
            log.import_date = datetime.now()
            session.commit()
            session.refresh(log)
        return log
    
    @staticmethod
    def delete_log(session: Session, file_name: str) -> bool:
        """Supprimer un log"""
        log = session.get(ImportLog, file_name)
        if log:
            session.delete(log)
            session.commit()
            return True
        return False
    
    @staticmethod
    def get_logs_by_status(session: Session, status: str) -> List[ImportLog]:
        """Récupérer les logs par statut"""
        statement = select(ImportLog).where(ImportLog.status == status)
        return session.exec(statement).all()
    
    @staticmethod
    def get_logs_by_date_range(session: Session, start_date: datetime, end_date: datetime) -> List[ImportLog]:
        """Récupérer les logs dans une plage de dates"""
        statement = select(ImportLog).where(
            ImportLog.import_date >= start_date,
            ImportLog.import_date <= end_date
        )
        return session.exec(statement).all()
    
    @staticmethod
    def get_recent_logs(session: Session, limit: int = 10) -> List[ImportLog]:
        """Récupérer les logs récents"""
        statement = select(ImportLog).order_by(ImportLog.import_date.desc()).limit(limit)
        return session.exec(statement).all()


class TaxiTripService:
    """Service pour les opérations CRUD des trajets taxi"""
    
    @staticmethod
    def get_trip(db: Session, trip_id: int) -> Optional[YellowTaxiTrip]:
        """Récupérer un trajet par ID"""
        return db.get(YellowTaxiTrip, trip_id)
    
    @staticmethod
    def get_trips(db: Session, skip: int, limit: int) -> Tuple[List[YellowTaxiTrip], int]:
        """Récupérer une liste de trajets avec pagination"""
        # Récupérer le total des trajets
        total_count = db.exec(select(func.count(YellowTaxiTrip.id))).one()
        
        # Récupérer les trajets avec pagination
        statement = select(YellowTaxiTrip).offset(skip).limit(limit)
        trips = db.exec(statement).all()
        
        return trips, total_count
    
    @staticmethod
    def create_trip(db: Session, trip: TaxiTripCreate) -> YellowTaxiTrip:
        """Créer un nouveau trajet"""
        # Convertir le schéma en dictionnaire et exclure les valeurs None
        trip_data = trip.model_dump(exclude_unset=True)
        db_trip = YellowTaxiTrip(**trip_data)
        db.add(db_trip)
        db.commit()
        db.refresh(db_trip)
        return db_trip
    
    @staticmethod
    def update_trip(db: Session, trip_id: int, trip: TaxiTripUpdate) -> Optional[YellowTaxiTrip]:
        """Mettre à jour un trajet existant"""
        db_trip = db.get(YellowTaxiTrip, trip_id)
        if not db_trip:
            return None
        
        # Convertir le schéma en dictionnaire et exclure les valeurs None
        trip_data = trip.model_dump(exclude_unset=True)
        
        for key, value in trip_data.items():
            setattr(db_trip, key, value)
        
        db.commit()
        db.refresh(db_trip)
        return db_trip
    
    @staticmethod
    def delete_trip(db: Session, trip_id: int) -> bool:
        """Supprimer un trajet"""
        db_trip = db.get(YellowTaxiTrip, trip_id)
        if not db_trip:
            return False
        
        db.delete(db_trip)
        db.commit()
        return True
    
    @staticmethod
    def get_statistics(db: Session) -> Statistics:
        """Calculer les statistiques (COUNT, MIN, MAX, AVG)"""
        # Statistiques de distance
        distance_stats = db.exec(select(
            func.count(YellowTaxiTrip.trip_distance).label('count'),
            func.min(YellowTaxiTrip.trip_distance).label('min_distance'),
            func.max(YellowTaxiTrip.trip_distance).label('max_distance'),
            func.avg(YellowTaxiTrip.trip_distance).label('avg_distance')
        )).one()
        
        # Statistiques de tarif
        fare_stats = db.exec(select(
            func.min(YellowTaxiTrip.total_amount).label('min_fare'),
            func.max(YellowTaxiTrip.total_amount).label('max_fare'),
            func.avg(YellowTaxiTrip.total_amount).label('avg_fare')
        )).one()
        
        # Statistiques de passagers
        passenger_stats = db.exec(select(
            func.min(YellowTaxiTrip.passenger_count).label('min_passengers'),
            func.max(YellowTaxiTrip.passenger_count).label('max_passengers'),
            func.avg(YellowTaxiTrip.passenger_count).label('avg_passengers')
        )).one()
        
        return Statistics(
            count=distance_stats.count,
            min_distance=distance_stats.min_distance,
            max_distance=distance_stats.max_distance,
            avg_distance=distance_stats.avg_distance,
            min_fare=fare_stats.min_fare,
            max_fare=fare_stats.max_fare,
            avg_fare=fare_stats.avg_fare,
            min_passengers=passenger_stats.min_passengers,
            max_passengers=passenger_stats.max_passengers,
            avg_passengers=passenger_stats.avg_passengers
        )


# Fonctions utilitaires pour la gestion des sessions
def get_session():
    """Créer une nouvelle session de base de données"""
    return Session(engine)


def close_session(session: Session):
    """Fermer une session de base de données"""
    session.close()


# Exemples d'utilisation
if __name__ == "__main__":
    # Exemple d'utilisation du CRUD
    with get_session() as session:
        # Créer un log d'importation
        log = ImportLogCRUD.create_log(session, "test_file.parquet", "success")
        print(f"Log créé: {log}")
        
        # Récupérer les statistiques des voyages
        stats = TaxiTripService.get_statistics(session)
        print(f"Statistiques: {stats}")
        
        # Récupérer quelques trajets
        trips, total = TaxiTripService.get_trips(session, skip=0, limit=5)
        print(f"Trajets récupérés: {len(trips)} sur {total}")
