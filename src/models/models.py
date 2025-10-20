from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

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