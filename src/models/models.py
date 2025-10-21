from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional, Tuple, List

class YellowTaxiTrip(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    vendorid: Optional[int] = Field(default=None)
    tpep_pickup_datetime: Optional[datetime] = Field(default=None)
    tpep_dropoff_datetime: Optional[datetime] = Field(default=None) 
    passenger_count: Optional[float] = Field(default=None)
    trip_distance: Optional[float] = Field(default=None)
    ratecodeid: Optional[float] = Field(default=None)
    store_and_fwd_flag: Optional[str] = Field(default=None, max_length=1)
    pulocationid: Optional[int] = Field(default=None)
    dolocationid: Optional[int] = Field(default=None)
    payment_type: Optional[int] = Field(default=None)
    fare_amount: Optional[float] = Field(default=None)
    extra: Optional[float] = Field(default=None)
    mta_tax: Optional[float] = Field(default=None)
    tip_amount: Optional[float] = Field(default=None)
    tolls_amount: Optional[float] = Field(default=None)
    improvement_surcharge: Optional[float] = Field(default=None)
    total_amount: Optional[float] = Field(default=None)
    congestion_surcharge: Optional[float] = Field(default=None)
    airport_fee: Optional[float] = Field(default=None)
    cbd_congestion_fee: Optional[float] = Field(default=None)

class ImportLog(SQLModel, table=True):
    file_name: str = Field(default=None, primary_key=True)
    import_date: datetime = Field(default=None)
    status: str = Field(default=None)

# Schémas pour les opérations CRUD
class TaxiTripCreate(SQLModel):
    vendorid: Optional[int] = None
    tpep_pickup_datetime: Optional[datetime] = None
    tpep_dropoff_datetime: Optional[datetime] = None
    passenger_count: Optional[float] = None
    trip_distance: Optional[float] = None
    ratecodeid: Optional[float] = None
    store_and_fwd_flag: Optional[str] = None
    pulocationid: Optional[int] = None
    dolocationid: Optional[int] = None
    payment_type: Optional[int] = None
    fare_amount: Optional[float] = None
    extra: Optional[float] = None
    mta_tax: Optional[float] = None
    tip_amount: Optional[float] = None
    tolls_amount: Optional[float] = None
    improvement_surcharge: Optional[float] = None
    total_amount: Optional[float] = None
    congestion_surcharge: Optional[float] = None
    airport_fee: Optional[float] = None
    cbd_congestion_fee: Optional[float] = None

class TaxiTripUpdate(SQLModel):
    vendorid: Optional[int] = None
    tpep_pickup_datetime: Optional[datetime] = None
    tpep_dropoff_datetime: Optional[datetime] = None
    passenger_count: Optional[float] = None
    trip_distance: Optional[float] = None
    ratecodeid: Optional[float] = None
    store_and_fwd_flag: Optional[str] = None
    pulocationid: Optional[int] = None
    dolocationid: Optional[int] = None
    payment_type: Optional[int] = None
    fare_amount: Optional[float] = None
    extra: Optional[float] = None
    mta_tax: Optional[float] = None
    tip_amount: Optional[float] = None
    tolls_amount: Optional[float] = None
    improvement_surcharge: Optional[float] = None
    total_amount: Optional[float] = None
    congestion_surcharge: Optional[float] = None
    airport_fee: Optional[float] = None
    cbd_congestion_fee: Optional[float] = None

class Statistics(SQLModel):
    count: int
    min_distance: Optional[float] = None
    max_distance: Optional[float] = None
    avg_distance: Optional[float] = None
    min_fare: Optional[float] = None
    max_fare: Optional[float] = None
    avg_fare: Optional[float] = None
    min_passengers: Optional[float] = None
    max_passengers: Optional[float] = None
    avg_passengers: Optional[float] = None