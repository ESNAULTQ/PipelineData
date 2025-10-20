from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
from src.models.models import YellowTaxiTrip, ImportLog
from src.database import engine


class YellowTaxiTripCRUD:
    """CRUD operations for YellowTaxiTrip model"""
    
    @staticmethod
    def create_trip(session: Session, trip_data: dict) -> YellowTaxiTrip:
        """Créer un nouveau voyage taxi"""
        trip = YellowTaxiTrip(**trip_data)
        session.add(trip)
        session.commit()
        session.refresh(trip)
        return trip
    
    @staticmethod
    def get_trip_by_id(session: Session, trip_id: int) -> Optional[YellowTaxiTrip]:
        """Récupérer un voyage par son ID"""
        return session.get(YellowTaxiTrip, trip_id)
    
    @staticmethod
    def get_all_trips(session: Session, skip: int = 0, limit: int = 100) -> List[YellowTaxiTrip]:
        """Récupérer tous les voyages avec pagination"""
        statement = select(YellowTaxiTrip).offset(skip).limit(limit)
        return session.exec(statement).all()
    
    @staticmethod
    def update_trip(session: Session, trip_id: int, trip_data: dict) -> Optional[YellowTaxiTrip]:
        """Mettre à jour un voyage"""
        trip = session.get(YellowTaxiTrip, trip_id)
        if trip:
            for key, value in trip_data.items():
                setattr(trip, key, value)
            session.commit()
            session.refresh(trip)
        return trip
    
    @staticmethod
    def delete_trip(session: Session, trip_id: int) -> bool:
        """Supprimer un voyage"""
        trip = session.get(YellowTaxiTrip, trip_id)
        if trip:
            session.delete(trip)
            session.commit()
            return True
        return False
    
    @staticmethod
    def get_trips_by_date_range(session: Session, start_date: datetime, end_date: datetime) -> List[YellowTaxiTrip]:
        """Récupérer les voyages dans une plage de dates"""
        statement = select(YellowTaxiTrip).where(
            YellowTaxiTrip.tpep_pickup_datetime >= start_date,
            YellowTaxiTrip.tpep_pickup_datetime <= end_date
        )
        return session.exec(statement).all()
    
    @staticmethod
    def get_trips_by_location(session: Session, pickup_location: int, dropoff_location: int = None) -> List[YellowTaxiTrip]:
        """Récupérer les voyages par localisation"""
        statement = select(YellowTaxiTrip).where(YellowTaxiTrip.pulocationid == pickup_location)
        if dropoff_location:
            statement = statement.where(YellowTaxiTrip.dolocationid == dropoff_location)
        return session.exec(statement).all()
    
    @staticmethod
    def get_trips_by_payment_type(session: Session, payment_type: int) -> List[YellowTaxiTrip]:
        """Récupérer les voyages par type de paiement"""
        statement = select(YellowTaxiTrip).where(YellowTaxiTrip.payment_type == payment_type)
        return session.exec(statement).all()
    
    @staticmethod
    def get_trips_by_distance_range(session: Session, min_distance: float, max_distance: float) -> List[YellowTaxiTrip]:
        """Récupérer les voyages par distance"""
        statement = select(YellowTaxiTrip).where(
            YellowTaxiTrip.trip_distance >= min_distance,
            YellowTaxiTrip.trip_distance <= max_distance
        )
        return session.exec(statement).all()
    
    @staticmethod
    def get_trips_by_fare_range(session: Session, min_fare: float, max_fare: float) -> List[YellowTaxiTrip]:
        """Récupérer les voyages par montant de course"""
        statement = select(YellowTaxiTrip).where(
            YellowTaxiTrip.total_amount >= min_fare,
            YellowTaxiTrip.total_amount <= max_fare
        )
        return session.exec(statement).all()
    
    @staticmethod
    def get_trips_with_passengers(session: Session, min_passengers: int = 1) -> List[YellowTaxiTrip]:
        """Récupérer les voyages avec passagers"""
        statement = select(YellowTaxiTrip).where(YellowTaxiTrip.passenger_count >= min_passengers)
        return session.exec(statement).all()
    
    @staticmethod
    def get_statistics(session: Session) -> dict:
        """Récupérer les statistiques générales"""
        total_trips = session.exec(select(func.count(YellowTaxiTrip.id))).one()
        avg_distance = session.exec(select(func.avg(YellowTaxiTrip.trip_distance))).one()
        avg_fare = session.exec(select(func.avg(YellowTaxiTrip.total_amount))).one()
        avg_passengers = session.exec(select(func.avg(YellowTaxiTrip.passenger_count))).one()
        
        return {
            "total_trips": total_trips,
            "average_distance": avg_distance,
            "average_fare": avg_fare,
            "average_passengers": avg_passengers
        }
    
    @staticmethod
    def get_top_pickup_locations(session: Session, limit: int = 10) -> List[dict]:
        """Récupérer les principales zones de prise en charge"""
        statement = select(
            YellowTaxiTrip.pulocationid,
            func.count(YellowTaxiTrip.id).label("trip_count")
        ).group_by(YellowTaxiTrip.pulocationid).order_by(func.count(YellowTaxiTrip.id).desc()).limit(limit)
        
        results = session.exec(statement).all()
        return [{"location_id": r.pulocationid, "trip_count": r.trip_count} for r in results]
    
    @staticmethod
    def get_top_dropoff_locations(session: Session, limit: int = 10) -> List[dict]:
        """Récupérer les principales zones de dépose"""
        statement = select(
            YellowTaxiTrip.dolocationid,
            func.count(YellowTaxiTrip.id).label("trip_count")
        ).group_by(YellowTaxiTrip.dolocationid).order_by(func.count(YellowTaxiTrip.id).desc()).limit(limit)
        
        results = session.exec(statement).all()
        return [{"location_id": r.dolocationid, "trip_count": r.trip_count} for r in results]


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
        stats = YellowTaxiTripCRUD.get_statistics(session)
        print(f"Statistiques: {stats}")
        
        # Récupérer les principales zones de prise en charge
        top_pickup = YellowTaxiTripCRUD.get_top_pickup_locations(session, 5)
        print(f"Top pickup locations: {top_pickup}")
